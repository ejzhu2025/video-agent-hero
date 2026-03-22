"""web/server.py — FastAPI app setup, startup, settings, and HTML serving."""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

# Load .env from project root, then from the persistent data volume (HF Spaces).
# The data-volume copy takes precedence so user-saved keys survive container rebuilds.
load_dotenv()
_data_env = Path(os.environ.get("VAH_DATA_DIR", "./data")) / ".env"
if _data_env.exists():
    load_dotenv(_data_env, override=True)

# Add project root to path so we can import agent.*
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

import agent.deps as deps
from web.brand_kit_api import router as brand_kit_router
from web.auth.router import router as auth_router
from web.billing.router import router as billing_router
from web.feedback_api import router as feedback_router
from web.routers.projects import router as projects_router
from web.routers.scrape import router as scrape_router
from web.templates import _HTML
from web.landing import _LANDING_HTML
from web.legal import PRIVACY_HTML, TERMS_HTML
from web.tiktok import router as tiktok_router

app = FastAPI(title="Video Agent Hero")

# ── CORS ──────────────────────────────────────────────────────────────────────
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://adreel.studio",
        "https://www.adreel.studio",
        # Cloud Run direct URLs (used during testing / before custom domain resolves)
        "https://ads-video-hero-716019218505.us-central1.run.app",
        "https://ads-video-hero-staging-716019218505.us-central1.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(brand_kit_router)
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(feedback_router)
app.include_router(projects_router)
app.include_router(scrape_router)
app.include_router(tiktok_router)

from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "adreel-session-secret"))


# ── HTTPS redirect middleware ─────────────────────────────────────────────────
from fastapi import Request
from fastapi.responses import RedirectResponse as _Redirect

@app.middleware("http")
async def https_redirect(request: Request, call_next):
    # Cloud Run forwards the original scheme in X-Forwarded-Proto
    proto = request.headers.get("x-forwarded-proto", "https")
    if proto == "http":
        url = request.url.replace(scheme="https")
        return _Redirect(str(url), status_code=301)
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ── Startup ───────────────────────────────────────────────────────────────────


@app.on_event("startup")
async def startup():
    deps.init()
    # Start midnight feedback analysis loop
    asyncio.create_task(_start_analysis_loop())
    # Auto-seed brand kit + user prefs so the app works out of the box
    try:
        from memory.schemas import (
            BrandKit, UserPrefs, LogoConfig, ColorPalette, FontConfig,
            SubtitleStyle, IntroOutro,
        )
        from scripts.create_assets import create_placeholder_logo
        db = deps.db()
        logo_path = create_placeholder_logo()
        tong_sui = BrandKit(
            brand_id="tong_sui", name="Tong Sui",
            logo=LogoConfig(path=str(logo_path), safe_area="top_right"),
            colors=ColorPalette(primary="#00B894", secondary="#FFFFFF",
                                accent="#FF7675", background="#1A1A2E"),
            fonts=FontConfig(title="Poppins-SemiBold", body="Inter-Regular"),
            subtitle_style=SubtitleStyle(
                position="bottom_center", box_opacity=0.55, box_radius=12,
                padding_px=14, max_chars_per_line=18, highlight_keywords=True, font_size=44,
            ),
            intro_outro=IntroOutro(
                intro_template="mint_splash", outro_cta="Order now",
                intro_duration_sec=1.5, outro_duration_sec=2.0,
            ),
        )
        if not db.get_brand_kit("tong_sui"):
            db.upsert_brand_kit(tong_sui)
        ej = UserPrefs(
            user_id="ej", default_platform="tiktok", preferred_duration_sec=20,
            tone=["fresh", "playful", "premium"], pacing="fast", shot_density=7, cta_style="soft",
        )
        if not db.get_user_prefs("ej"):
            db.upsert_user_prefs(ej)
    except Exception as e:
        print(f"[startup] brand kit seed skipped: {e}", flush=True)


async def _start_analysis_loop():
    from web.feedback_analysis import daily_analysis_loop
    await daily_analysis_loop()


# ── Request models ────────────────────────────────────────────────────────────


class ApiKeyRequest(BaseModel):
    anthropic_api_key: str = ""
    fal_key: str = ""
    replicate_api_token: str = ""
    google_api_key: str = ""


# ── Settings & utility endpoints ──────────────────────────────────────────────


@app.post("/api/init")
async def init_db():
    """Initialize DB with sample Tong Sui brand kit."""
    from memory.schemas import (
        BrandKit, UserPrefs, LogoConfig, ColorPalette, FontConfig,
        SubtitleStyle, IntroOutro,
    )
    from scripts.create_assets import create_placeholder_logo

    db = deps.db()
    logo_path = create_placeholder_logo()
    tong_sui = BrandKit(
        brand_id="tong_sui",
        name="Tong Sui",
        logo=LogoConfig(path=str(logo_path), safe_area="top_right"),
        colors=ColorPalette(
            primary="#00B894", secondary="#FFFFFF",
            accent="#FF7675", background="#1A1A2E",
        ),
        fonts=FontConfig(title="Poppins-SemiBold", body="Inter-Regular"),
        subtitle_style=SubtitleStyle(
            position="bottom_center", box_opacity=0.55, box_radius=12,
            padding_px=14, max_chars_per_line=18, highlight_keywords=True, font_size=44,
        ),
        intro_outro=IntroOutro(
            intro_template="mint_splash", outro_cta="Order now",
            intro_duration_sec=1.5, outro_duration_sec=2.0,
        ),
    )
    db.upsert_brand_kit(tong_sui)
    ej = UserPrefs(
        user_id="ej", default_platform="tiktok", preferred_duration_sec=20,
        tone=["fresh", "playful", "premium"], pacing="fast", shot_density=7, cta_style="soft",
    )
    db.upsert_user_prefs(ej)
    return {"status": "ok", "message": "DB initialized with Tong Sui brand kit"}


def _mask_key(key: str) -> str:
    return f"{key[:8]}…{key[-4:]}" if len(key) > 12 else ("set" if key else "")


def _upsert_env_file(env_path: Path, updates: dict[str, str]) -> None:
    """Write/update key=value pairs in a .env file without touching other lines."""
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    for var in updates:
        lines = [l for l in lines if not l.startswith(f"{var}=")]
    for var, val in updates.items():
        lines.append(f"{var}={val}")
    env_path.write_text("\n".join(lines) + "\n")


@app.get("/api/changelog")
async def get_changelog():
    """Return changelog entries from git log (auto-updated on every commit)."""
    import re
    import subprocess
    import json as _json

    _PREFIX = re.compile(
        r"^(feat|fix|chore|refactor|docs|test|style|perf|ci|build)(\([^)]+\))?:\s*",
        re.IGNORECASE,
    )
    _SKIP = re.compile(
        r"update changelog|merge (branch|pull)|co-authored|bump version",
        re.IGNORECASE,
    )

    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%ad|%s", "--date=short", "--no-merges", "-40"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=5,
        )
        entries = []
        seen = set()
        for line in result.stdout.splitlines():
            date, sep, msg = line.partition("|")
            if not sep or _SKIP.search(msg):
                continue
            text = _PREFIX.sub("", msg).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            entries.append({"date": date.strip(), "text": text})
        if entries:
            return entries
    except Exception:
        pass

    # Fallback: static file
    p = Path(__file__).parent / "changelog.json"
    if p.exists():
        return _json.loads(p.read_text())
    return []


@app.get("/api/settings")
async def get_settings():
    """Return current settings (keys masked)."""
    ant_key = os.environ.get("ANTHROPIC_API_KEY", "")
    fal_key = os.environ.get("FAL_KEY", "") or os.environ.get("FAL_API_KEY", "")
    rep_token = os.environ.get("REPLICATE_API_TOKEN", "")
    google_key = os.environ.get("GOOGLE_API_KEY", "")
    return {
        "anthropic_api_key_set": bool(ant_key),
        "anthropic_api_key_preview": _mask_key(ant_key),
        "fal_key_set": bool(fal_key),
        "fal_key_preview": _mask_key(fal_key),
        "replicate_api_token_set": bool(rep_token),
        "replicate_api_token_preview": _mask_key(rep_token),
        "google_api_key_set": bool(google_key),
        "google_api_key_preview": _mask_key(google_key),
    }


@app.post("/api/settings")
async def save_settings(req: ApiKeyRequest):
    """Set API keys for this session and persist to .env."""
    ant_key = req.anthropic_api_key.strip()
    fal_key = req.fal_key.strip()
    google_key_check = req.google_api_key.strip()
    if not ant_key and not fal_key and not google_key_check:
        raise HTTPException(status_code=400, detail="At least one API key must be provided")
    data_dir = Path(os.environ.get("VAH_DATA_DIR", str(Path(__file__).parent.parent / "data")))
    data_dir.mkdir(parents=True, exist_ok=True)
    env_path = data_dir / ".env"
    updates: dict[str, str] = {}
    replicate_token = req.replicate_api_token.strip()
    google_key = req.google_api_key.strip()
    if ant_key:
        os.environ["ANTHROPIC_API_KEY"] = ant_key
        updates["ANTHROPIC_API_KEY"] = ant_key
    if fal_key:
        os.environ["FAL_KEY"] = fal_key
        updates["FAL_KEY"] = fal_key
    if replicate_token:
        os.environ["REPLICATE_API_TOKEN"] = replicate_token
        updates["REPLICATE_API_TOKEN"] = replicate_token
    if google_key:
        os.environ["GOOGLE_API_KEY"] = google_key
        updates["GOOGLE_API_KEY"] = google_key
    _upsert_env_file(env_path, updates)
    return {
        "status": "ok",
        "anthropic_preview": _mask_key(ant_key) if ant_key else None,
        "fal_preview": _mask_key(fal_key) if fal_key else None,
        "replicate_preview": _mask_key(replicate_token) if replicate_token else None,
        "google_preview": _mask_key(google_key) if google_key else None,
    }


@app.get("/demos/{filename}")
async def serve_demo(filename: str):
    """Serve bundled demo videos."""
    if not filename.endswith(".mp4") or "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    demo_path = Path(__file__).parent / "static" / "demos" / filename
    if not demo_path.exists():
        raise HTTPException(status_code=404, detail="Demo not found")
    return FileResponse(demo_path, media_type="video/mp4")


@app.get("/video/{filename}")
async def serve_video(filename: str):
    """Serve a video file from the exports directory."""
    if not filename.endswith(".mp4") or "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    data_dir = os.environ.get("VAH_DATA_DIR", str(Path(__file__).parent.parent / "data"))
    video_path = Path(data_dir) / "exports" / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(video_path, media_type="video/mp4")


# ── HTML frontend ─────────────────────────────────────────────────────────────


_ASSETS_DIR = Path(__file__).parent.parent / "assets"


@app.get("/favicon.png")
async def favicon_png():
    return FileResponse(_ASSETS_DIR / "adreel_favicon.png", media_type="image/png")


@app.get("/favicon.ico")
async def favicon_ico():
    return FileResponse(_ASSETS_DIR / "adreel_favicon.png", media_type="image/png")


@app.get("/logo.png")
async def logo_png():
    return FileResponse(_ASSETS_DIR / "adreel_logo.png", media_type="image/png")


@app.get("/", response_class=HTMLResponse)
async def landing():
    return _LANDING_HTML


@app.get("/privacy", response_class=HTMLResponse)
async def privacy():
    return PRIVACY_HTML


@app.get("/terms", response_class=HTMLResponse)
async def terms():
    return TERMS_HTML


@app.get("/app", response_class=HTMLResponse)
async def index():
    return _HTML


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)
