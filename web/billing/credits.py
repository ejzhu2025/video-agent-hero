"""billing/credits.py — Credit balance operations on the users table."""
from __future__ import annotations

import agent.deps as deps
from web.auth.models import ensure_schema


def get_credits(user_id: str) -> int:
    ensure_schema()
    with deps.db()._conn() as conn:
        row = conn.execute(
            "SELECT credits FROM users WHERE id=?", (user_id,)
        ).fetchone()
    return row[0] if row else 0


def add_credits(user_id: str, amount: int) -> int:
    """Add credits to user (e.g. after successful payment). Returns new balance."""
    ensure_schema()
    with deps.db()._conn() as conn:
        conn.execute(
            "UPDATE users SET credits = credits + ? WHERE id=?",
            (amount, user_id),
        )
        row = conn.execute(
            "SELECT credits FROM users WHERE id=?", (user_id,)
        ).fetchone()
    return row[0] if row else 0


def fulfill_session(session_id: str, user_id: str, credits: int) -> tuple[bool, int]:
    """Idempotent credit fulfillment for a Stripe checkout session.

    Returns (was_new, new_balance). If session already fulfilled, returns (False, current_balance).
    """
    ensure_schema()
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    with deps.db()._conn() as conn:
        existing = conn.execute(
            "SELECT credits FROM fulfilled_sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if existing:
            row = conn.execute("SELECT credits FROM users WHERE id=?", (user_id,)).fetchone()
            return False, (row[0] if row else 0)
        conn.execute(
            "INSERT INTO fulfilled_sessions (session_id, user_id, credits, fulfilled_at) VALUES (?,?,?,?)",
            (session_id, user_id, credits, now),
        )
        conn.execute(
            "UPDATE users SET credits = credits + ? WHERE id=?", (credits, user_id)
        )
        row = conn.execute("SELECT credits FROM users WHERE id=?", (user_id,)).fetchone()
    return True, (row[0] if row else 0)


def deduct_credits(user_id: str, amount: int) -> int:
    """Deduct credits. Raises ValueError if balance insufficient. Returns new balance."""
    ensure_schema()
    with deps.db()._conn() as conn:
        row = conn.execute(
            "SELECT credits FROM users WHERE id=?", (user_id,)
        ).fetchone()
        balance = row[0] if row else 0
        if balance < amount:
            raise ValueError(f"Insufficient credits: have {balance}, need {amount}")
        conn.execute(
            "UPDATE users SET credits = credits - ? WHERE id=?",
            (amount, user_id),
        )
        return balance - amount


# ── Cost table ────────────────────────────────────────────────────────────────

COSTS = {
    "shot_turbo": 1,
    "shot_hd":    3,
    "flux_kontext": 1,
}


def cost_for_plan(shot_count: int, quality: str = "turbo") -> int:
    per_shot = COSTS["shot_hd"] if quality == "hd" else COSTS["shot_turbo"]
    return shot_count * per_shot
