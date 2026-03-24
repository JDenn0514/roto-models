"""
Shared authentication for OnRoto scrapers.

Loads credentials from .env and provides a login function
that returns an authenticated session with session_id.
"""

import os
import re
import requests
from dotenv import load_dotenv

# Load .env from the project root
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

BASE_URL = os.environ["ONROTO_BASE_URL"]
LEAGUE = os.environ["ONROTO_LEAGUE"]
USERNAME = os.environ["ONROTO_USERNAME"]
PASSWORD = os.environ["ONROTO_PASSWORD"]


def login() -> tuple[requests.Session, str]:
    """
    Log in to OnRoto and return (session, session_id).
    """
    session = requests.Session()
    session.get(f"{BASE_URL}/")
    resp = session.post(
        f"{BASE_URL}/index.pl",
        data={
            "user": USERNAME,
            "pass": PASSWORD,
            "submit": "Login",
            "postback": "1",
        },
        allow_redirects=True,
    )
    resp.raise_for_status()

    match = re.search(r"session_id=([A-Za-z0-9]+)", resp.url)
    if not match:
        match = re.search(r"session_id=([A-Za-z0-9]+)", resp.text)
    if not match:
        raise RuntimeError("Could not extract session_id after login")

    return session, match.group(1)
