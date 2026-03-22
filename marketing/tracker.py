"""marketing/tracker.py — record campaigns, posts, and pull analytics."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_DB = Path(__file__).parent / "data" / "marketing.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Tracker:
    def __init__(self, db_path: Path | str | None = None):
        self.db_path = Path(db_path or _DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id          TEXT PRIMARY KEY,
                    brand       TEXT NOT NULL,
                    url         TEXT NOT NULL,
                    size        TEXT NOT NULL DEFAULT 'small',
                    category    TEXT NOT NULL DEFAULT '',
                    video_path  TEXT NOT NULL DEFAULT '',
                    output_dir  TEXT NOT NULL DEFAULT '',
                    brief       TEXT NOT NULL DEFAULT '',
                    created_at  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS posts (
                    id          TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL REFERENCES campaigns(id),
                    platform    TEXT NOT NULL,
                    post_id     TEXT NOT NULL DEFAULT '',
                    posted_at   TEXT,
                    views       INTEGER DEFAULT 0,
                    likes       INTEGER DEFAULT 0,
                    comments    INTEGER DEFAULT 0,
                    saves       INTEGER DEFAULT 0,
                    dms         INTEGER DEFAULT 0,
                    synced_at   TEXT,
                    notes       TEXT DEFAULT ''
                );
            """)

    # ── Write ─────────────────────────────────────────────────────────────────

    def record_campaign(
        self,
        brand: str,
        url: str,
        size: str,
        category: str,
        video_path: str,
        output_dir: str,
        brief: str = "",
        campaign_id: str | None = None,
    ) -> str:
        import uuid
        cid = campaign_id or f"camp_{uuid.uuid4().hex[:10]}"
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO campaigns
                   (id, brand, url, size, category, video_path, output_dir, brief, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (cid, brand, url, size, category, video_path, output_dir, brief, _now()),
            )
        return cid

    def record_post(
        self,
        campaign_id: str,
        platform: str,
        post_id: str = "",
        notes: str = "",
    ) -> str:
        import uuid
        pid = f"post_{uuid.uuid4().hex[:10]}"
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO posts (id, campaign_id, platform, post_id, posted_at, notes)
                   VALUES (?,?,?,?,?,?)""",
                (pid, campaign_id, platform, post_id, _now(), notes),
            )
        return pid

    def update_post_stats(
        self,
        post_id: str,
        views: int = 0,
        likes: int = 0,
        comments: int = 0,
        saves: int = 0,
        dms: int = 0,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """UPDATE posts SET views=?, likes=?, comments=?, saves=?, dms=?, synced_at=?
                   WHERE id=?""",
                (views, likes, comments, saves, dms, _now(), post_id),
            )

    # ── Instagram Graph API sync ───────────────────────────────────────────────

    def sync_instagram(self, post_id_in_db: str, ig_media_id: str) -> dict[str, Any] | None:
        """Pull metrics from Instagram Graph API and update the post record.

        Requires INSTAGRAM_ACCESS_TOKEN env var.
        """
        token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        if not token:
            print("[tracker] INSTAGRAM_ACCESS_TOKEN not set — skipping sync")
            return None

        try:
            import httpx
            resp = httpx.get(
                f"https://graph.instagram.com/v21.0/{ig_media_id}/insights",
                params={
                    "metric": "impressions,reach,likes,comments,saved,video_views",
                    "access_token": token,
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[tracker] Instagram sync failed: {e}")
            return None

        metrics: dict[str, int] = {}
        for item in data.get("data", []):
            metrics[item["name"]] = item.get("values", [{}])[0].get("value", 0)

        self.update_post_stats(
            post_id=post_id_in_db,
            views=metrics.get("video_views", metrics.get("impressions", 0)),
            likes=metrics.get("likes", 0),
            comments=metrics.get("comments", 0),
            saves=metrics.get("saved", 0),
        )
        return metrics

    # ── Report ────────────────────────────────────────────────────────────────

    def report(self) -> list[dict[str, Any]]:
        """Return aggregated stats grouped by brand size and platform."""
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT
                    c.size,
                    p.platform,
                    COUNT(DISTINCT c.id)        AS campaigns,
                    COUNT(p.id)                 AS posts,
                    SUM(p.views)                AS total_views,
                    ROUND(AVG(p.views), 0)      AS avg_views,
                    ROUND(AVG(p.likes), 0)      AS avg_likes,
                    SUM(p.dms)                  AS total_dms,
                    ROUND(
                        100.0 * SUM(p.dms) / NULLIF(COUNT(p.id), 0), 2
                    )                           AS dm_rate_pct
                FROM campaigns c
                LEFT JOIN posts p ON p.campaign_id = c.id
                GROUP BY c.size, p.platform
                ORDER BY c.size, p.platform
            """).fetchall()
        return [dict(r) for r in rows]

    def list_campaigns(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM campaigns ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_campaign_posts(self, campaign_id: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM posts WHERE campaign_id=? ORDER BY posted_at DESC",
                (campaign_id,),
            ).fetchall()
        return [dict(r) for r in rows]
