"""web/tiktok.py — TikTok Content Posting API integration."""
from __future__ import annotations

import os
import secrets
import urllib.parse
from pathlib import Path

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

router = APIRouter(prefix="/tiktok")

_CLIENT_KEY    = os.getenv("TIKTOK_CLIENT_KEY", "")
_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
_REDIRECT_URI  = "https://adreel.studio/tiktok/callback"
_SCOPES        = "video.publish,video.list"

# In-memory token store (sufficient for demo; replace with DB for production)
_tokens: dict[str, str] = {}   # state → access_token after callback
_user_token: dict = {}          # {"access_token": ..., "open_id": ...}


# ── OAuth: start ──────────────────────────────────────────────────────────────

@router.get("/auth")
async def tiktok_auth(request: Request):
    """Redirect user to TikTok OAuth consent screen."""
    state = secrets.token_urlsafe(16)
    request.session["tiktok_state"] = state

    params = {
        "client_key":     _CLIENT_KEY,
        "response_type":  "code",
        "scope":          _SCOPES,
        "redirect_uri":   _REDIRECT_URI,
        "state":          state,
    }
    url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode(params)
    return RedirectResponse(url)


# ── OAuth: callback ───────────────────────────────────────────────────────────

@router.get("/callback")
async def tiktok_callback(request: Request, code: str = "", error: str = "", state: str = ""):
    """Handle TikTok OAuth callback, exchange code for access token."""
    if error:
        return HTMLResponse(f"<p>TikTok auth error: {error}</p>")

    expected_state = request.session.get("tiktok_state", "")
    if state != expected_state:
        return HTMLResponse("<p>Invalid state. Please try again.</p>", status_code=400)

    # Exchange code for token
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://open.tiktokapis.com/v2/oauth/token/",
                data={
                    "client_key":     _CLIENT_KEY,
                    "client_secret":  _CLIENT_SECRET,
                    "code":           code,
                    "grant_type":     "authorization_code",
                    "redirect_uri":   _REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        return HTMLResponse(f"<p>Token exchange failed: {e}</p>", status_code=500)

    _user_token["access_token"] = data.get("access_token", "")
    _user_token["open_id"]      = data.get("open_id", "")

    return HTMLResponse("""
    <html><head><script>
      window.opener && window.opener.postMessage('tiktok_authed', '*');
      window.close();
    </script></head>
    <body style="background:#000;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh">
      <p>Connected to TikTok. You can close this window.</p>
    </body></html>
    """)


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/status")
async def tiktok_status():
    """Check whether TikTok is connected."""
    connected = bool(_user_token.get("access_token"))
    return {"connected": connected}


# ── Post video ────────────────────────────────────────────────────────────────

@router.post("/post")
async def tiktok_post(request: Request):
    """Initiate a TikTok video upload via Content Posting API (PULL_FROM_URL)."""
    body = await request.json()
    video_filename = body.get("filename", "")
    caption        = body.get("caption", "")

    access_token = _user_token.get("access_token", "")
    if not access_token:
        return JSONResponse({"error": "Not connected to TikTok"}, status_code=401)

    video_url = f"https://adreel.studio/video/{video_filename}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type":  "application/json; charset=UTF-8",
    }
    payload = {
        "post_info": {
            "title":          caption[:150],
            "privacy_level":  "SELF_ONLY",   # sandbox: private only
            "disable_duet":   False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source":        "PULL_FROM_URL",
            "video_url":     video_url,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://open.tiktokapis.com/v2/post/publish/video/init/",
                json=payload,
                headers=headers,
            )
            data = resp.json()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    if data.get("error", {}).get("code", "ok") != "ok":
        return JSONResponse({"error": data["error"].get("message", "Unknown error")}, status_code=400)

    publish_id = data.get("data", {}).get("publish_id", "")
    return {"ok": True, "publish_id": publish_id}


# ── List videos ───────────────────────────────────────────────────────────────

@router.get("/videos")
async def tiktok_videos():
    """List videos published via this app (video.list scope)."""
    access_token = _user_token.get("access_token", "")
    if not access_token:
        return JSONResponse({"error": "Not connected"}, status_code=401)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://open.tiktokapis.com/v2/video/list/",
                json={"max_count": 20},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json; charset=UTF-8",
                },
            )
            data = resp.json()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    videos = data.get("data", {}).get("videos", [])
    return {"videos": videos}
