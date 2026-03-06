"""billing/router.py — /api/billing/* endpoints: plans, checkout, webhook."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from web.auth.deps import current_user
from web.auth.models import User
from web.billing.credits import add_credits, get_credits
from web.billing.stripe_client import PLANS, create_checkout_session, verify_webhook

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])


# ── Plans ─────────────────────────────────────────────────────────────────────

@router.get("/plans")
def list_plans():
    """Return available credit packages (public — no auth needed)."""
    return [
        {k: v for k, v in p.items() if k != "stripe_price_id"}
        for p in PLANS
    ]


# ── Checkout ──────────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan_id: str


@router.post("/checkout")
def create_checkout(body: CheckoutRequest, user: User = Depends(current_user)):
    """Create a Stripe Checkout Session and return the redirect URL."""
    try:
        url = create_checkout_session(body.plan_id, user.id, user.email)
        return {"url": url}
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        logger.error("Stripe checkout error: %s", exc)
        raise HTTPException(502, "Payment service unavailable")


# ── Balance ───────────────────────────────────────────────────────────────────

@router.get("/balance")
def balance(user: User = Depends(current_user)):
    return {"credits": get_credits(user.id)}


# ── Webhook ───────────────────────────────────────────────────────────────────

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default="", alias="stripe-signature"),
):
    """Stripe calls this after a successful payment. Adds credits to user."""
    payload = await request.body()
    try:
        event = verify_webhook(payload, stripe_signature)
    except Exception as exc:
        logger.warning("Webhook signature verification failed: %s", exc)
        raise HTTPException(400, "Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata", {})
        user_id = meta.get("user_id")
        credits = int(meta.get("credits", 0))

        if user_id and credits > 0:
            new_balance = add_credits(user_id, credits)
            logger.info(
                "Credits added: user=%s credits=%d new_balance=%d",
                user_id, credits, new_balance,
            )

    # Always return 200 so Stripe doesn't retry
    return {"received": True}
