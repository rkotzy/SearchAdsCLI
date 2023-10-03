import typer
import re
import os
from searchadscli.utils.config import get_config, save_config
from rich.table import Table
from rich.console import Console


def configure(
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
    config = get_config() if not all else {}

    # Flags list to check if any individual flag is set
    individual_flags = [private_key_file, client_id, team_id, key_id, org_id, app_id]

    # If any individual flag is set, update only that and return
    if any(individual_flags):
        if private_key_file:
            private_key_file = validate_pem_file(private_key_file, "private key file")
            config["private_key_file"] = private_key_file
        if client_id:
            client_id = validate_searchads_id(client_id, "client_id")
            config["client_id"] = client_id
        if team_id:
            team_id = validate_searchads_id(team_id, "team_id")
            config["team_id"] = team_id
        if key_id:
            key_id = validate_key_id(key_id)
            config["key_id"] = key_id
        if org_id:
            config["org_id"] = org_id
        if app_id:
            config["app_id"] = app_id

    else:  # No individual flags set, check for missing values
        if not config.get("private_key_file"):
            private_key_file = typer.prompt(
                "Path to private key file", default="private-key.pem"
            ).strip()
            private_key_file = validate_pem_file(private_key_file, "private key file")
            config["private_key_file"] = private_key_file

        if not config.get("client_id"):
            client_id = typer.prompt("Client ID").strip()
            client_id = validate_searchads_id(client_id, "client_id")
            config["client_id"] = client_id

        if not config.get("team_id"):
            team_id = typer.prompt("Team ID").strip()
            team_id = validate_searchads_id(team_id, "team_id")
            config["team_id"] = team_id

        if not config.get("key_id"):
            key_id = typer.prompt("Key ID").strip()
            key_id = validate_key_id(key_id)
            config["key_id"] = key_id
        if not config.get("org_id"):
            org_id = typer.prompt("Apple Search Ads Organization ID").strip()
            config["org_id"] = org_id

        if not config.get("app_id"):
            app_id = typer.prompt(
                "Apple ID of the app you wish to run campaigns for (e.g. id571800810)"
            ).strip()
            app_id = validate_app_id(app_id)
            config["app_id"] = app_id

    # Save the updated config
    save_config(config)

    # After saving the new configuration, clear the access_token_expiry value
    if "access_token_expiry" in ctx.obj:
        del ctx.obj["access_token_expiry"]

    console = Console()

    # Create a new table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Config", style="dim", width=50)
    table.add_column("Value")

    # Populate the table with data from the config object
    for key, value in config.items():
        table.add_row(key, str(value))

    # Print the table
    console.print(table)
    console.print("Configuration saved successfully!", style="bold")


def validate_pem_file(file_path: str, file_type: str) -> str:
    while not (file_path.endswith(".pem") and os.path.exists(file_path)):
        typer.echo(
            f"Invalid {file_type}. Please provide a valid .pem file path that exists."
        )
        file_path = typer.prompt(f"Path to {file_type}", default="private-key.pem")
    return file_path


def validate_searchads_id(value: str, id_type: str) -> str:
    pattern = re.compile(
        r"^SEARCHADS\.[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
    )
    while not pattern.match(value):
        typer.echo(
            f"Invalid {id_type}. Please provide a valid ID in the format 'SEARCHADS.<UUID>'."
        )
        value = typer.prompt(f"{id_type}")
    return value


def validate_key_id(value: str) -> str:
    pattern = re.compile(
        r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
    )
    while not pattern.match(value):
        typer.echo("Invalid key_id. Please provide a valid UUID.")
        value = typer.prompt("key_id")
    return value


def validate_app_id(value: str) -> int:
    app_id = value[2:] if value.startswith("id") else value

    if app_id.isnumeric():
        return int(app_id)
    else:
        typer.echo("Invalid app_id. Please provide a valid Apple App ID.")
        value = typer.prompt("app_id")
        return validate_app_id(value)
