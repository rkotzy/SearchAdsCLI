import typer
from typing_extensions import Annotated
from searchadscli.utils.config import get_config, check_config_values, CampaignType
from searchadscli.commands.campaign import list_campaigns, create_campaigns
from searchadscli.commands.keywords import add_keywords as add_keywords_cmd
from searchadscli.commands.keywords import add_negative_keywords as add_negative_keywords_cmd
from searchadscli.commands.configure import configure as configure_cmd


app = typer.Typer(rich_markup_mode="rich")


def validate_campaign_type(value: CampaignType) -> CampaignType:
    try:
        if value in {CampaignType.exact, CampaignType.competitor}:
            print(value)
            return value
        else:
            raise ValueError(f"{value} is not an allowed campaign type.")
    except ValueError as e:
        raise typer.BadParameter(str(e))


@app.callback()
def main(ctx: typer.Context):
    """Apple Search Ads CLI: A simple CLI to get started with Apple Search Ads Advanced."""
    config = get_config()
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


@app.command()
def config(
    ctx: typer.Context,
    all: bool = typer.Option(
        False, help="Request all configuration values, overwriting existing ones."
    ),
    private_key_file: str = typer.Option(
        None, "--private-key-file", help="Path to private key file."
    ),
    client_id: str = typer.Option(None, "--client-id", help="Client ID."),
    team_id: str = typer.Option(None, "--team-id", help="Team ID."),
    key_id: str = typer.Option(None, "--key-id", help="Key ID."),
    org_id: str = typer.Option(None, "--org-id", help="Organization ID."),
    app_id: int = typer.Option(None, "--app-id", help="Apple App ID."),
):
    """Set up the CLI with necessary authentication details."""
    configure_cmd(
        ctx, all, private_key_file, client_id, team_id, key_id, org_id, app_id
    )


@app.command()
def get_campaigns(ctx: typer.Context):
    """Fetch and display the names of Apple Search Ads campaigns."""
    check_config_values(ctx)
    list_campaigns(ctx)


@app.command()
def setup_campaigns(ctx: typer.Context):
    """Setup a new 3 campaign structure in given countries."""
    check_config_values(ctx)
    create_campaigns(ctx)


@app.command()
def add_keywords(
    ctx: typer.Context,
    type: CampaignType = typer.Option(
        default=CampaignType.exact,
        case_sensitive=False,
        help="Provide 'exact' (default) or 'competitor' argument",
    ),
):
    """Add keywords to a campaign."""
    if type == CampaignType.discovery:
        typer.echo("Error: 'discovery' is not an allowed campaign type.")
        raise typer.Exit(code=1)

    check_config_values(ctx)
    add_keywords_cmd(ctx, type)


@app.command()
def add_negative_keywords(ctx: typer.Context):
    """Add negative keywords to all campaigns"""

    check_config_values(ctx)
    add_negative_keywords_cmd(ctx)


if __name__ == "__main__":
    app()
