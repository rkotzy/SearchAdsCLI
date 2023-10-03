import typer
from searchadscli.utils.adgroups_api import get_adgroups
from searchadscli.utils.config import get_org_id, CampaignType, CAMPAIGN_STRUCTURE, CAMPAIGN_PREFIX
from searchadscli.utils.campaigns_api import find_active_campaigns
from searchadscli.utils.keywords_api import (
    add_keywords_to_adgroup_api,
    remove_keywords_from_adgroup_api,
    add_negative_keywords_to_campaign_api,
    remove_negative_keywords_from_campaign_api,
)
from rich import print
from rich.table import Table
from rich.console import Console
from rich.prompt import Prompt


def add_keywords(ctx: typer.Context, type: CampaignType):
    org_id = get_org_id(ctx)
    console = Console()
    with console.status("[dots2]Finding campaigns..."):
        find_campaign_response = find_active_campaigns(ctx, org_id, None, type)

    if find_campaign_response.status_code != 200:
        console.print(
            f"[red]Error fetching campaigns. Status code: {find_campaign_response.status_code}[/red]"
        )
        raise typer.Exit(code=1)

    all_campaigns = find_campaign_response.json().get("data", [])

    if not all_campaigns:
        console.print(
            f"[red]No active SearchAdsCLI campaigns found for type: {type.value}[/red]"
        )
        raise typer.Exit(code=1)

    table = Table(title="Campaigns")

    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Campaign Name", style="magenta")

    for idx, campaign in enumerate(all_campaigns, 1):
        table.add_row(str(idx), campaign["name"])

    console.print(table)

    while True:
        choice = input("Choose a campaign by number: ")
        if choice.isdigit() and 1 <= int(choice) <= len(all_campaigns):
            break
        console.print("[red]Invalid input! Please choose a valid number.[/red]")

    selected_campaign = all_campaigns[int(choice) - 1]
    console.print(f"You chose: [green]{selected_campaign['name']}[/green]")

    campaigns = find_campaign_set_from(ctx, org_id, type, selected_campaign["name"])
    campaigns[type] = selected_campaign

    keywords = prompt_for_keywords()

    if type == CampaignType.exact:
        add_keywords_to_exact(ctx, org_id, campaigns, keywords)
        remove_keywords_from_competitor(ctx, org_id, campaigns, keywords)
        add_keywords_to_discovery(ctx, org_id, campaigns, keywords)
    elif type == CampaignType.competitor:
        add_keywords_to_competitor(ctx, org_id, campaigns, keywords)
        remove_keywords_from_exact(ctx, org_id, campaigns, keywords)
        add_keywords_to_discovery(ctx, org_id, campaigns, keywords)
    else:
        console.print(f"[red]Unknown campaign type.[/red]")
        raise typer.Exit(code=1)


def add_negative_keywords(ctx: typer.Context):
    org_id = get_org_id(ctx)

    with Console().status("[dots2]Fetching campaigns..."):
        campaigns_reponse = find_active_campaigns(ctx, org_id)

    if campaigns_reponse.status_code != 200:
        typer.echo(
            f"Failed to fetch campaigns. Status Code: {campaigns_reponse.status_code}"
        )
        typer.Exit(code=1)

    data = campaigns_reponse.json()

    keywords = prompt_for_keywords()

    with Console().status("[dots2]Adding negative keywords to campaigns..."):
        for campaign in data.get("data", []):
            add_negative_keywords_to_campaign_api(ctx, org_id, campaign["id"], keywords)


def check_keywords():
    # Run an audit on all keywords
    # Makes sure there's no exact match keywords in the discovery-broad campaign
    # Checks that all exact match keywords are negative keywords in search match campaign
    pass


def find_campaign_set_from(
    ctx: typer.Context, org_id: str, type: CampaignType, name: str
):
    countries_string = name.split("_")[-1]
    countries_string = countries_string.split("-")[0]

    lookup_campaigns = [CampaignType.discovery]

    if type == CampaignType.exact:
        lookup_campaigns.append(CampaignType.competitor)
    elif type == CampaignType.competitor:
        lookup_campaigns.append(CampaignType.exact)

    lookup_names = [
        f"{CAMPAIGN_PREFIX}_{lookup_type.value}_{countries_string}-{ctx.obj['config'].get('app_id')}"
        for lookup_type in lookup_campaigns
    ]

    with Console().status("[dots2]Finding campaign set..."):
        find_campaign_response = find_active_campaigns(
            ctx, org_id, None, None, lookup_names
        ).json()

    if find_campaign_response.get("error"):
        typer.echo("Error:", find_campaign_response["error"])
        raise typer.Exit(code=1)

    result = {}
    for item in find_campaign_response.get("data", []):
        if CampaignType.discovery in item["name"]:
            result[CampaignType.discovery] = item
        elif CampaignType.exact in item["name"]:
            result[CampaignType.exact] = item
        elif CampaignType.competitor in item["name"]:
            result[CampaignType.competitor] = item

    return result


def validate_keywords(keywords: list[str]) -> list[str]:
    sanitized_keywords = []

    for keyword in keywords:
        sanitized_keyword = keyword.strip().lower()

        if sanitized_keyword not in sanitized_keywords:
            sanitized_keywords.append(sanitized_keyword)

    if len(sanitized_keywords) > 100:
        typer.echo("Error: Please provide 100 or less keywords at a time.")
        raise typer.Exit(code=1)

    return sanitized_keywords


def validate_expected_adgroups(campaign_adgroups_data, expected_adgroups):
    fetched_names = {adgroup["name"] for adgroup in campaign_adgroups_data["data"]}

    expected_names = {adgroup["name"] for adgroup in expected_adgroups}

    if fetched_names == expected_names:
        return True
    else:
        missing_in_fetched = expected_names - fetched_names
        extra_in_fetched = fetched_names - expected_names
        return False, {
            "missing_in_fetched": missing_in_fetched,
            "extra_in_fetched": extra_in_fetched,
        }


def prompt_for_keywords():
    console = Console()

    keywords_prompt = "Enter a comma separated list of keywords (or phrases)"
    console.print(keywords_prompt, style="bold")

    sanitized_keywords = []

    while not sanitized_keywords:
        keyword_input = Prompt.ask("Keywords")

        keywords_list = [k for k in keyword_input.split(",") if k]

        try:
            sanitized_keywords = validate_keywords(keywords_list)
            if sanitized_keywords:
                console.print(
                    f"You entered [bold]{len(sanitized_keywords)}[/bold] unique keywords: {', '.join(sanitized_keywords)}"
                )
            else:
                console.print("[yellow]Please enter at least one keyword.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

    return sanitized_keywords


def add_keywords_to_exact(
    ctx: typer.Context, org_id: str, campaigns: dict, keywords: list[str]
):
    add_keywords_to_campaign(ctx, org_id, campaigns, keywords, CampaignType.exact)


def remove_keywords_from_exact(
    ctx: typer.Context, org_id: str, campaigns: dict, keywords: list[str]
):
    remove_keywords_from_campaign(ctx, org_id, campaigns, keywords, CampaignType.exact)


def add_keywords_to_discovery(
    ctx: typer.Context, org_id: str, campaigns: dict, keywords: list[str]
):
    add_keywords_to_campaign(ctx, org_id, campaigns, keywords, CampaignType.discovery)
    add_negative_keywords_to_campaign(
        ctx, org_id, campaigns, keywords, CampaignType.discovery
    )


def add_keywords_to_competitor(
    ctx: typer.Context, org_id: str, campaigns: dict, keywords: list[str]
):
    add_keywords_to_campaign(ctx, org_id, campaigns, keywords, CampaignType.competitor)


def remove_keywords_from_competitor(
    ctx: typer.Context, org_id: str, campaigns: dict, keywords: list[str]
):
    remove_keywords_from_campaign(
        ctx, org_id, campaigns, keywords, CampaignType.competitor
    )


def add_keywords_to_campaign(
    ctx: typer.Context,
    org_id: str,
    campaigns: dict,
    keywords: list[str],
    type: CampaignType,
):
    campaign = campaigns[type]
    campaign_id = campaign["id"]
    adgroups = CAMPAIGN_STRUCTURE[type].get("adgroups", [])

    with Console().status("[dots2]Finding campaign adgroups..."):
        campaign_adgroups_response = get_adgroups(ctx, org_id, campaign_id).json()

    if campaign_adgroups_response.get("error"):
        errors = campaign_adgroups_response["error"].get("errors", [])

        for error in errors:
            print(error.get("message", "Unknown error"))
        raise typer.Exit(code=1)

    campaign_adgroups = campaign_adgroups_response.get("data", [])

    for adgroup in adgroups:
        if "matchType" in adgroup:
            for campaign_adgroup in campaign_adgroups:
                if adgroup["name"] == campaign_adgroup["name"]:
                    add_keywords_response = add_keywords_to_adgroup_api(
                        ctx,
                        org_id,
                        campaign_id,
                        campaign_adgroup["id"],
                        keywords,
                        adgroup["matchType"],
                    )

                    if add_keywords_response.status_code != 200:
                        add_keywords_response_data = add_keywords_response.json()
                        if add_keywords_response_data.get("error"):
                            errors = add_keywords_response_data["error"].get(
                                "errors", []
                            )

                            for error in errors:
                                print(error.get("message", "Unknown error"))


def remove_keywords_from_campaign(
    ctx: typer.Context,
    org_id: str,
    campaigns: dict,
    keywords: list[str],
    type: CampaignType,
):
    campaign = campaigns[type]
    campaign_id = campaign["id"]
    adgroups = CAMPAIGN_STRUCTURE[type].get("adgroups", [])

    with Console().status("[dots2]Finding campaign adgroups..."):
        campaign_adgroups_response = get_adgroups(ctx, org_id, campaign_id).json()

    if campaign_adgroups_response.get("error"):
        errors = campaign_adgroups_response["error"].get("errors", [])

        for error in errors:
            print(error.get("message", "Unknown error"))
        raise typer.Exit(code=1)

    campaign_adgroups = campaign_adgroups_response.get("data", [])

    for adgroup in adgroups:
        for campaign_adgroup in campaign_adgroups:
            if adgroup["name"] == campaign_adgroup["name"]:
                remove_keywords_response = remove_keywords_from_adgroup_api(
                    ctx,
                    org_id,
                    campaign_id,
                    campaign_adgroup["id"],
                    keywords,
                )

                if remove_keywords_response.status_code != 200:
                    remove_keywords_response_data = remove_keywords_response.json()
                    if remove_keywords_response_data.get("error"):
                        errors = remove_keywords_response_data["error"].get(
                            "errors", []
                        )

                        for error in errors:
                            print(error.get("message", "Unknown error"))


def add_negative_keywords_to_campaign(
    ctx: typer.Context,
    org_id: str,
    campaigns: dict,
    keywords: list[str],
    type: CampaignType,
):
    campaign = campaigns[type]
    campaign_id = campaign["id"]

    add_negative_keywords_response = add_negative_keywords_to_campaign_api(
        ctx, org_id, campaign_id, keywords
    )

    if add_negative_keywords_response.status_code != 200:
        add_negative_keywords_response_data = add_negative_keywords_response.json()
        if add_negative_keywords_response_data.get("error"):
            errors = add_negative_keywords_response_data["error"].get("errors", [])

            for error in errors:
                print(error.get("message", "Unknown error"))


def remove_negative_keywords_from_campaign(
    ctx: typer.Context,
    org_id: str,
    campaigns: dict,
    keywords: list[str],
    type: CampaignType,
):
    campaign = campaigns[type]
    campaign_id = campaign["id"]

    remove_negative_keywords_response = remove_negative_keywords_from_campaign_api(
        ctx, org_id, campaign_id, keywords
    )

    if remove_negative_keywords_response.status_code != 200:
        remove_negative_keywords_response_data = (
            remove_negative_keywords_response.json()
        )
        if remove_negative_keywords_response_data.get("error"):
            errors = remove_negative_keywords_response_data["error"].get("errors", [])

            for error in errors:
                print(error.get("message", "Unknown error"))
