import requests
import logging

def generate_token():
    token_url = "your_token_url"
    client_id = "your_client_id"
    client_secret = "your_client_secret"

    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "Mulescale"
    }

    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Token generation error: {e}")
        return None
