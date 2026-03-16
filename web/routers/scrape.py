"""web/routers/scrape.py — /api/scrape-product endpoint."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ScrapeRequest(BaseModel):
    url: str


@router.post("/api/scrape-product")
async def scrape_product_endpoint(req: ScrapeRequest):
    from agent.nodes.planner_llm import get_gemini_client
    from web.scrape_product import scrape_product

    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    data_dir = Path(os.environ.get("VAH_DATA_DIR", "./data"))
    gemini_client = get_gemini_client()

    result = await scrape_product(url, data_dir, gemini_client)
    return result
