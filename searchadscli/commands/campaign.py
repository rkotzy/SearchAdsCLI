import typer
from searchadscli.utils.campaigns_api import (
    find_active_campaigns,
    pause_campaign,
    get_campaigns,
    create_campaign,
)
from searchadscli.utils.adgroups_api import create_adgroup
from searchadscli.utils.config import get_org_id, CAMPAIGN_STRUCTURE, CampaignType
from rich.table import Table
from rich.console import Console
from rich.prompt import Prompt
from rich.prompt import IntPrompt
from rich.prompt import FloatPrompt
from rich.panel import Panel


def list_campaigns(ctx: typer.Context):
    """
    Fetch and display the names of Apple Search Ads campaigns.
    """

    orgId = get_org_id(ctx)

    console = Console()

    with console.status("[dots2]Fetching campaigns..."):
        response = get_campaigns(ctx, orgId)

    if response.status_code == 200:
        data = response.json()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Id")
        table.add_column("Name")
        table.add_column("Daily Budget")
        table.add_column("Status")

        for campaign in data.get("data", []):
            daily_budget = f"{campaign['dailyBudgetAmount']['amount']} {campaign['dailyBudgetAmount']['currency']}"
            name = campaign["name"]
            formatted_name = name[:50] + "..." if len(name) > 50 else name
            table.add_row(
                str(campaign["id"]),
                formatted_name,
                daily_budget,
                campaign["displayStatus"],
            )

        console.print(table)

    else:
        typer.echo(f"Failed to fetch campaigns. Status Code: {response.status_code}")


def create_campaigns(ctx: typer.Context):
    """
    Setup a new 3 campaign structure in given countries.
    """

    orgId = get_org_id(ctx)

    adam_id = ctx.obj["config"].get("app_id")
    if not adam_id:
        typer.echo("Error: app_id not set. Please run `searchads configure`.")
        raise typer.Exit(code=1)

    console = Console()

    targeting_prompt()
    countries = ask_country_targeting()

    with console.status("[dots2]Checking for any active campaigns..."):
        response = find_active_campaigns(ctx, orgId, countries)

    if response.status_code == 200:
        enabled_campaigns = response.json().get("data", [])

        if enabled_campaigns:
            for camp in enabled_campaigns:
                typer.echo(
                    f"Campaign: {camp['name']} - Status: {camp['displayStatus']}"
                )

            confirmation = Prompt.ask(
                "Do you want to pause all enabled campaigns in these countries first?",
                choices=["Y", "n"],
                default="Y",
            )
            if confirmation.lower() == "y":
                campaign_ids_to_pause = [
                    campaign["id"] for campaign in enabled_campaigns
                ]
                for campaign_id in campaign_ids_to_pause:
                    response = pause_campaign(ctx, orgId, campaign_id)

                    if response.status_code == 200:
                        typer.echo(f"Campaign {campaign_id} paused successfully!")
                    else:
                        typer.echo(
                            f"Failed to pause campaign {campaign_id}. Status Code: {response.text}"
                        )
                        raise typer.Exit(code=1)

        # Targeting criteria limits results, so let's hold off on this for now
        # device = ask_device_targeting()
        # age_min = ask_age_targeting("min")
        # age_max = ask_age_targeting("max")
        # gender = ask_for_gender_targeting()
        default_bid = ask_for_default_bid()
        discovery_budget = ask_budget(CampaignType.discovery)
        competitor_budget = ask_budget(CampaignType.competitor)
        exact_budget = ask_budget(CampaignType.exact)

        campaign_budgets = {
            CampaignType.discovery: discovery_budget,
            CampaignType.competitor: competitor_budget,
            CampaignType.exact: exact_budget,
        }

        success_messages = []
        error_messages = []

        with console.status("[dots2]Creating campaigns..."):
            for campaign_type, budget in campaign_budgets.items():
                response = create_campaign(
                    ctx, orgId, adam_id, budget, countries, campaign_type
                )

                response_data = response.json()

                if response and not response_data.get("error"):
                    campaign_data = response_data.get("data", {})
                    campaign_id = campaign_data.get("id")

                    if campaign_id:
                        campaign_adgroups = CAMPAIGN_STRUCTURE[campaign_type].get(
                            "adgroups", []
                        )

                        for adgroup in campaign_adgroups:
                            adgroup_response = create_adgroup(
                                ctx,
                                orgId,
                                campaign_id,
                                adgroup.get("name"),
                                default_bid,
                                adgroup.get("searchMatch", False),
                            )

                            adgroup_data = adgroup_response.json()

                            if adgroup_response and not adgroup_data.get("error"):
                                success_messages.append(
                                    f"Successfully created {adgroup.get('name')} adgroup for {campaign_type.value} campaign with ID: {campaign_id}"
                                )
                            else:
                                error_messages.append(
                                    f"Failed to create ad groups of type {adgroup.get('name')} for {campaign_type.value} campaign. Error: {adgroup_data.get('error')}"
                                )
                    else:
                        error_messages.append(
                            f"Unexpected response structure while creating {campaign_type.value} campaign. No ID found."
                        )
                else:
                    error_messages.append(
                        f"Failed to create {campaign_type.value} campaign. Error: {response_data.get('error')}"
                    )

        for message in success_messages:
            console.print(Panel(message, style="green", title="Success"))

        for message in error_messages:
            console.print(Panel(message, style="red", title="Error"))

        console.print("Campaign creation process finished!", style="bold")

        warning_message = (
            "Do not modify any campaign or ad group names from the Apple Search Ads dashboard."
            "\nThe SearchAds CLI relies on a particular naming convention for keyword management."
        )
        console.print(
            Panel(
                warning_message,
                title="Warning",
                style="bold yellow",
                border_style="yellow",
            )
        )
    else:
        typer.echo(f"Error finding campaigns. Status code: {response.text}")


def targeting_prompt():
    console = Console()

    ascii_art = """

   _____                      __    ___       __    
  / ___/___  ____ ___________/ /_  /   | ____/ /____
  \__ \/ _ \/ __ `/ ___/ ___/ __ \/ /| |/ __  / ___/
 ___/ /  __/ /_/ / /  / /__/ / / / ___ / /_/ (__  ) 
/____/\___/\__,_/_/   \___/_/ /_/_/  |_\__,_/____/  
                  
    """

    console.print(ascii_art, style="purple")

    prompt_text = """We'll ask some basic targeting questions to configure three (3) campaigns for your app.
    
If you need more advanced targeting, you can use the Search Ads Advanced dashboard or open a Github issue. You'll be able to review all campaigns before they are created.

Refer to the documentation for more information.
"""

    console.print(Panel(prompt_text, title="Campaign Setup", expand=False))
    console.input("[bold]Press any key to continue...[/bold]")


def ask_country_targeting():
    console = Console()

    country_prompt = "Enter a comma separated list of country codes where you want your campaigns to run"
    console.print(country_prompt, style="bold")

    countries_input = Prompt.ask("Country codes", default="US")

    country_list = [country.strip().upper() for country in countries_input.split(",")]
    console.print(f"Country targeting set to: {country_list}", style="bold green")
    console.print()
    return country_list


def ask_device_targeting():
    console = Console()
    prompt_text = """
Please choose a device to target:
1. iPhone
2. iPad
3. Both (default)
"""

    console.print(prompt_text)
    device_map = {"1": "IPHONE", "2": "IPAD", "3": "BOTH"}

    device_choice = Prompt.ask(
        "[bold]Enter the number corresponding to your choice[/bold]",
        choices=["1", "2", "3"],
        default="3",
    )

    while device_choice not in device_map.keys():
        console.print("Invalid choice. Please choose a number from 1 to 3.")
        device_choice = Prompt.ask(
            "[bold]Enter the number corresponding to your choice[/bold]",
            choices=["1", "2", "3"],
            default="3",
        )

    console.print(
        f"Device targeting set to {device_map[device_choice]}", style="bold green"
    )
    console.print()
    return device_map[device_choice]


def ask_age_targeting(age_type: str) -> int:
    console = Console()

    if age_type not in ["min", "max"]:
        raise ValueError("age_type must be either 'min' or 'max'")

    max_or_min = f"{age_type}imum".upper()
    age_prompt = f"Enter a {max_or_min} age for targeting, between 18-65, (or press Enter for no {age_type}):"

    while True:
        console.print(age_prompt, style="bold")

        age_value = IntPrompt.ask(f"Enter {age_type} age", default="")

        if not age_value:
            console.print(
                f"No {age_type} age set.",
                style="bold green",
            )
            console.print()
            return age_value
        elif 18 <= age_value <= 65:
            console.print(
                f"{age_type.capitalize()} age set to {age_value}",
                style="bold green",
            )
            console.print()
            return age_value
        else:
            console.print("Please enter a value between 18 and 65.", style="bold red")


def ask_for_gender_targeting():
    console = Console()
    prompt_text = """
Please choose a gender to target:
1. Female
2. Male
3. All (default)
    """

    console.print(prompt_text)
    gender_map = {"1": "F", "2": "M", "3": "ALL"}

    gender_choice = Prompt.ask(
        "[bold]Enter the number corresponding to your choice[/bold]",
        choices=["1", "2", "3"],
        default="3",
    )

    while gender_choice not in gender_map.keys():
        console.print("Invalid choice. Please choose a number from 1 to 3.")
        gender_choice = Prompt.ask(
            "[bold]Enter the number corresponding to your choice[/bold]",
            choices=["1", "2", "3"],
            default="3",
        )

    console.print(
        f"Gender targeting set to {gender_map[gender_choice]}", style="bold green"
    )
    console.print()
    return gender_map[gender_choice]


def ask_for_default_bid() -> float:
    console = Console()

    bid_prompt = (
        "[bold]Enter a default keyword bid in USD, between 0.01 and 100:[/bold]"
    )

    while True:
        bid_value = FloatPrompt.ask(bid_prompt, default=1.0)

        bid_value = round(bid_value, 2)

        if 0.01 <= bid_value <= 100:
            console.print(f"Default bid set to ${bid_value:.2f}", style="bold green")
            return bid_value
        else:
            console.print(
                "Please enter a value between 0.01 and 100.", style="bold red"
            )


def ask_budget(campaign_type: str) -> int:
    console = Console()

    default_budgets = {
        CampaignType.exact: 40,
        CampaignType.discovery: 10,
        CampaignType.competitor: 10,
    }

    budget_prompt = f"Enter a daily budget for {campaign_type.upper()} campaign, in USD"

    while True:
        console.print(budget_prompt, style="bold")

        default_value = default_budgets[campaign_type]

        budget_value = IntPrompt.ask(
            f"{campaign_type.capitalize()} campaign budget", default=default_value
        )

        if not budget_value or (5 <= budget_value <= 1000):
            console.print(
                f"{campaign_type.capitalize()} campaign budget set to ${budget_value}",
                style="bold green",
            )
            console.print()
            return budget_value

        console.print("Please enter a value between 5 and 1000.", style="bold red")
