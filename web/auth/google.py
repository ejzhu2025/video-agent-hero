"""auth/google.py — Google OAuth 2.0 Authorization Code flow (no authlib needed)."""
from __future__ import annotations

import os
import urllib.parse

import httpx

# ── Credentials (set via env vars in .env) ───────────────────────────────────
# 1. Go to https://console.cloud.google.com/apis/credentials
# 2. Create OAuth 2.0 Client ID (Web application)
# 3. Add Authorised redirect URIs: https://your-domain/auth/callback
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID",     "PLACEHOLDER_client_id")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "PLACEHOLDER_client_secret")
GOOGLE_REDIRECT_URI  = os.getenv("GOOGLE_REDIRECT_URI",  "http://localhost:8000/auth/callback")

_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def get_authorization_url(state: str) -> str:
    """Build the Google consent screen URL."""
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         state,
        "access_type":   "online",
        "prompt":        "select_account",
    }
    return f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code(code: str) -> dict:
    """Exchange auth code for tokens. Returns token dict."""
    with httpx.Client(timeout=10) as client:
        resp = client.post(_TOKEN_URL, data={
            "code":          code,
            "client_id":     GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri":  GOOGLE_REDIRECT_URI,
            "grant_type":    "authorization_code",
        })
        resp.raise_for_status()
        return resp.json()


def get_userinfo(access_token: str) -> dict:
    """Fetch the user's Google profile (sub, email, name, picture)."""
    with httpx.Client(timeout=10) as client:
        resp = client.get(
            _USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
