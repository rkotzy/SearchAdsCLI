import typer
import requests
from searchadscli.utils.access_token import get_access_token
from searchadscli.utils.config import CAMPAIGN_PREFIX, CampaignType


def find_active_campaigns(
    ctx: typer.Context,
    orgId: str,
    countries: list | None = None,
    type: CampaignType | None = None,
    names: list[str] | None = None,
):
    access_token = get_access_token(ctx)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={orgId}",
    }

    data = {
        "pagination": {"offset": 0, "limit": 1000},
        "conditions": [
            {"field": "servingStatus", "operator": "EQUALS", "values": ["RUNNING"]},
        ],
    }

    if names:
        condition = {"field": "name", "operator": "IN", "values": names}
        data["conditions"].append(condition)
    else:
        if type:
            data["conditions"].append(
                {
                    "field": "name",
                    "operator": "STARTSWITH",
                    "values": [f"{CAMPAIGN_PREFIX}_{type.value}"],
                }
            )

        if countries:
            data["conditions"].append(
                {
                    "field": "countriesOrRegions",
                    "operator": "CONTAINS_ALL",
                    "values": countries,
                }
            )

    return requests.post(
        "https://api.searchads.apple.com/api/v4/campaigns/find",
        headers=headers,
        json=data,
    )


def pause_campaign(ctx: typer.Context, orgId: str, campaign_id: str):
    access_token = get_access_token(ctx)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={orgId}",
    }
    data = {"campaign": {"status": "PAUSED"}}

    return requests.put(
        f"https://api.searchads.apple.com/api/v4/campaigns/{campaign_id}",
        headers=headers,
        json=data,
    )


def get_campaigns(ctx: typer.Context, orgId: str):
    access_token = get_access_token(ctx)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={orgId}",
    }
    return requests.get(
        "https://api.searchads.apple.com/api/v4/campaigns", headers=headers
    )


def create_campaign(
    ctx: typer.Context,
    orgId: str,
    app_id: int,
    daily_budget: int,
    countries: list[str],
    type: str,
):
    access_token = get_access_token(ctx)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={orgId}",
    }

    countries_string = "-".join(countries)
    name = f"{CAMPAIGN_PREFIX}_{type.value}_{countries_string}-{app_id}"

    data = {
        "adamId": app_id,
        "orgId": orgId,
        "adChannelType": "SEARCH",
        "billingEvent": "TAPS",
        "dailyBudgetAmount": {"amount": str(daily_budget), "currency": "USD"},
        "countriesOrRegions": countries,
        "name": name,
        "status": "ENABLED",
        "supplySources": ["APPSTORE_SEARCH_RESULTS"],
    }
    return requests.post(
        "https://api.searchads.apple.com/api/v4/campaigns",
        headers=headers,
        json=data,
    )
