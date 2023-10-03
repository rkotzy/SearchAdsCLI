import typer
import os
import json
from enum import Enum

CONFIG_PATH = os.path.expanduser("~/.searchads_cli_config.json")

REQUIRED_CONFIG_VALUES = [
    "private_key_file",
    "client_id",
    "team_id",
    "key_id",
    "org_id",
    "app_id",
]


class CampaignType(str, Enum):
    exact = "exact"
    discovery = "discovery"
    competitor = "competitor"


class MatchType(str, Enum):
    exact = "EXACT"
    broad = "BROAD"


CAMPAIGN_PREFIX = "SearchAdsCLI"
CAMPAIGN_STRUCTURE = {
    "exact": {
        "adgroups": [{"name": "Exact", "matchType": MatchType.exact}],
    },
    "discovery": {
        "adgroups": [
            {"name": "Discovery-Broad", "matchType": MatchType.broad},
            {"name": "Discovery-Search", "searchMatch": True},
        ],
    },
    "competitor": {
        "adgroups": [{"name": "Competitor-General", "matchType": MatchType.exact}],
    },
}


def get_org_id(ctx: typer.Context):
    orgId = ctx.obj["config"].get("org_id")
    if not orgId:
        typer.echo("Error: org_id not set. Please run `searchads config`.")
        raise typer.Exit(code=1)
    else:
        return orgId


def check_config_values(ctx: typer.Context):
    """Check if all required configuration values are set."""

    config = ctx.obj["config"]

    missing_values = [
        key for key in REQUIRED_CONFIG_VALUES if key not in config or not config[key]
    ]

    if missing_values:
        missing_values_str = ", ".join(missing_values)
        message = f"Missing config value(s) for: {missing_values_str}\n\nRun searchads config to set up"
        raise typer.Exit(message)

    return True


def get_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}


def save_config(conf):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(conf, f)
