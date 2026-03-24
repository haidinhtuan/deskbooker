"""
Authentication module for Deskbird API.

Uses Firebase's token exchange endpoint to convert a long-lived refresh token
into a short-lived access token that can be used to authenticate API requests.
"""
import json

import requests


def get_access_token(token_key, refresh_token):
    """Exchange a Firebase refresh token for a fresh access token.

    Args:
        token_key: Firebase API key (used as the 'key' query parameter).
        refresh_token: Firebase refresh token (long-lived, stored in .env).

    Returns:
        A short-lived access token string for use in Authorization headers.
    """
    url = "https://securetoken.googleapis.com/v1/token"
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

    response = requests.post(url, params={"key": token_key}, data=data)
    access_token = json.loads(response.text)["access_token"]
    return access_token
