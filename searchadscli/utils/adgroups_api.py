import typer
import requests
import datetime
from searchadscli.utils.access_token import get_access_token


def create_adgroup(
    ctx: typer.Context,
    orgId: str,
    campaign_id: str,
    name: str,
    default_bid: float,
    search_match: bool = False,
    age_min: int | None = None,
    age_max: int | None = None,
    gender: str = "ALL",
):
    access_token = get_access_token(ctx)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={orgId}",
    }

    current_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=5)
    formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    data = {
        "orgId": orgId,
        "name": name,
        "defaultBidAmount": {"amount": str(default_bid), "currency": "USD"},
        "pricingModel": "CPC",
        "status": "ENABLED",
        "startTime": formatted_time,
        "automatedKeywordsOptIn": search_match,
    }

    targeting_dimensions = {}

    if gender != "ALL":
        targeting_dimensions["gender"] = {"included": [gender]}

    if age_min or age_max:
        if not age_min:
            age_min = 18
        if not age_max:
            age_max = 65

        targeting_dimensions["age"] = {
            "included": [{"minAge": age_min, "maxAge": age_max}]
        }

    if targeting_dimensions:
        data["targetingDimensions"] = targeting_dimensions

    return requests.post(
        f"https://api.searchads.apple.com/api/v4/campaigns/{campaign_id}/adgroups",
        headers=headers,
        json=data,
    )


def get_adgroups(
    ctx: typer.Context,
    orgId: str,
    campaign_id: str,
):
    access_token = get_access_token(ctx)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={orgId}",
    }

    return requests.get(
        f"https://api.searchads.apple.com/api/v4/campaigns/{campaign_id}/adgroups",
        headers=headers,
    )
