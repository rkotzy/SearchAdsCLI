import os
import datetime as dt
import requests
from authlib.jose import jwt
from Crypto.PublicKey import ECC
import typer


def get_access_token(ctx: typer.Context):
    """
    Get a valid access token.
    If an existing token is still valid, return it.
    Otherwise, fetch a new one.
    """

    # Check if we already have an access_token and if it's still valid
    access_token_expiry = ctx.obj.get("access_token_expiry")
    if access_token_expiry:
        if dt.datetime.utcnow() < access_token_expiry:
            return ctx.obj.get("access_token")

    config = ctx.obj["config"]
    private_key_file = config["private_key_file"]
    client_id = config["client_id"]
    team_id = config["team_id"]
    key_id = config["key_id"]

    audience = "https://appleid.apple.com"
    alg = "ES256"

    # Load private key file.
    if os.path.isfile(private_key_file):
        with open(private_key_file, "rt") as file:
            private_key = ECC.import_key(file.read())
    else:
        typer.echo(
            "Error: invalid private key file. Please configure the CLI with `configure --private-key-file`"
        )
        if "private_key_file" in ctx.obj:
            del ctx.obj["private_key_file"]
        raise typer.Exit(code=1)

    # Define the issue timestamp.
    issued_at_timestamp = int(dt.datetime.utcnow().timestamp())
    # Define the expiration timestamp, which may not exceed 180 days from the issue timestamp.
    expiration_timestamp = issued_at_timestamp + 86400 * 180

    # Define the JWT headers.
    headers = dict()
    headers["alg"] = alg
    headers["kid"] = key_id

    # Define the JWT payload.
    payload = dict()
    payload["sub"] = client_id
    payload["aud"] = audience
    payload["iat"] = issued_at_timestamp
    payload["exp"] = expiration_timestamp
    payload["iss"] = team_id

    # Open the private key.
    with open(private_key_file, "rt") as file:
        private_key = ECC.import_key(file.read())

    client_secret = jwt.encode(
        header=headers, payload=payload, key=private_key.export_key(format="PEM")
    ).decode("UTF-8")

    # Now use client_secret to request access_token
    url = "https://appleid.apple.com/auth/oauth2/token"
    headers = {
        "Host": "appleid.apple.com",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": config["client_id"],
        "client_secret": client_secret,
        "scope": "searchadsorg",  # Assuming you always request this scope
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        response_json = response.json()
        access_token = response_json["access_token"]

        # Calculate token expiry time (subtracting 5 minutes for a buffer)
        token_lifetime = dt.timedelta(seconds=response_json["expires_in"] - 300)
        access_token_expiry = dt.datetime.utcnow() + token_lifetime

        ctx.obj["access_token"] = access_token
        ctx.obj["access_token_expiry"] = access_token_expiry

        return access_token
    else:
        typer.echo("Failed to obtain access token!")
        response.raise_for_status()
