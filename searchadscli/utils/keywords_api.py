import typer
import requests
from searchadscli.utils.config import MatchType
from searchadscli.utils.access_token import get_access_token


def add_keywords_to_adgroup_api(
    ctx: typer.Context,
    orgId: str,
    campaign_id: str,
    adgroup_id: str,
    keywords: list[str],
    match_type: MatchType,
):
    access_token = get_access_token(ctx)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={orgId}",
    }

    data = [{"text": keyword, "matchType": match_type.value} for keyword in keywords]

    return requests.post(
        f"https://api.searchads.apple.com/api/v4/campaigns/{campaign_id}/adgroups/{adgroup_id}/targetingkeywords/bulk",
        headers=headers,
        json=data,
    )


def remove_keywords_from_adgroup_api(
    ctx: typer.Context,
    orgId: str,
    campaign_id: str,
    adgroup_id: str,
    keywords: list[str],
):
    access_token = get_access_token(ctx)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={orgId}",
    }

    data = {
        "pagination": {"offset": 0, "limit": 1000},
        "conditions": [
            {"field": "adGroupId", "operator": "EQUALS", "values": [adgroup_id]},
            {"field": "text", "operator": "IN", "values": keywords},
        ],
    }

    keywords_response = requests.post(
        f"https://api.searchads.apple.com/api/v4/campaigns/{campaign_id}/adgroups/targetingkeywords/find",
        headers=headers,
        json=data,
    )

    if keywords_response.status_code != 200:
        return keywords_response

    keyword_ids = [item["id"] for item in keywords_response.json()["data"]]

    return requests.post(
        f"https://api.searchads.apple.com/api/v4/campaigns/{campaign_id}/adgroups/{adgroup_id}/targetingkeywords/delete/bulk",
        headers=headers,
        json=keyword_ids,
    )


def add_negative_keywords_to_campaign_api(
    ctx: typer.Context,
    orgId: str,
    campaign_id: str,
    keywords: list[str],
):
    access_token = get_access_token(ctx)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={orgId}",
    }

    data = [{"text": keyword, "matchType": "EXACT"} for keyword in keywords]

    return requests.post(
        f"https://api.searchads.apple.com/api/v4/campaigns/{campaign_id}/negativekeywords/bulk",
        headers=headers,
        json=data,
    )


def remove_negative_keywords_from_campaign_api(
    ctx: typer.Context,
    orgId: str,
    campaign_id: str,
    keywords: list[str],
):
    access_token = get_access_token(ctx)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-AP-Context": f"orgId={orgId}",
    }

    data = {
        "pagination": {"offset": 0, "limit": 1000},
        "conditions": [
            {"field": "text", "operator": "IN", "values": keywords},
        ],
    }

    keywords_response = requests.post(
        f"https://api.searchads.apple.com/api/v4/campaigns/{campaign_id}/negativekeywords/find",
        headers=headers,
        json=data,
    )

    if keywords_response.status_code != 200:
        return keywords_response
    
    keyword_ids = [item["id"] for item in keywords_response.json()["data"]]

    return requests.post(
        f"https://api.searchads.apple.com/api/v4/campaigns/{campaign_id}/negativekeywords/delete/bulk",
        headers=headers,
        json=keyword_ids,
    )
