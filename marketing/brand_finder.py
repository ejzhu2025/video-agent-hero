"""marketing/brand_finder.py — discover brand leads from multiple sources."""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import httpx

BrandSize = Literal["large", "medium", "small"]


@dataclass
class BrandLead:
    url: str
    name: str = ""
    category: str = ""
    size: BrandSize = "small"
    source: str = "manual"
    tagline: str = ""


# ── Product Hunt ──────────────────────────────────────────────────────────────

_PH_GRAPHQL = "https://api.producthunt.com/v2/api/graphql"

_PH_QUERY = """
query($first: Int!, $after: String) {
  posts(first: $first, after: $after, order: VOTES) {
    edges {
      node {
        name
        tagline
        website
        topics { edges { node { name } } }
        votesCount
      }
    }
    pageInfo { endCursor hasNextPage }
  }
}
"""


def find_from_product_hunt(count: int = 20, category: str = "") -> list[BrandLead]:
    """Fetch top products from Product Hunt. Requires PRODUCT_HUNT_TOKEN env var."""
    token = os.getenv("PRODUCT_HUNT_TOKEN", "")
    if not token:
        print("[brand_finder] PRODUCT_HUNT_TOKEN not set — skipping Product Hunt")
        return []

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    leads: list[BrandLead] = []
    after = None

    while len(leads) < count:
        variables: dict = {"first": min(20, count - len(leads))}
        if after:
            variables["after"] = after

        try:
            resp = httpx.post(
                _PH_GRAPHQL,
                json={"query": _PH_QUERY, "variables": variables},
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[brand_finder] Product Hunt request failed: {e}")
            break

        posts = data.get("data", {}).get("posts", {})
        edges = posts.get("edges", [])

        for edge in edges:
            node = edge["node"]
            url = node.get("website", "")
            if not url or not url.startswith("http"):
                continue

            topics = [
                t["node"]["name"].lower()
                for t in node.get("topics", {}).get("edges", [])
            ]
            cat = topics[0] if topics else "startup"

            if category and category.lower() not in topics:
                continue

            votes = node.get("votesCount", 0)
            size: BrandSize = "large" if votes > 1000 else "medium" if votes > 200 else "small"

            leads.append(BrandLead(
                url=url,
                name=node.get("name", ""),
                tagline=node.get("tagline", ""),
                category=cat,
                size=size,
                source="product_hunt",
            ))

        page_info = posts.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        after = page_info.get("endCursor")

    return leads[:count]


# ── CSV import ────────────────────────────────────────────────────────────────

def find_from_csv(path: str) -> list[BrandLead]:
    """Load brand leads from a CSV file.

    Expected columns: url (required), name, category, size, tagline
    """
    leads: list[BrandLead] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("url", "").strip()
            if not url:
                continue
            size_raw = row.get("size", "small").strip().lower()
            size: BrandSize = size_raw if size_raw in ("large", "medium", "small") else "small"
            leads.append(BrandLead(
                url=url,
                name=row.get("name", "").strip(),
                category=row.get("category", "").strip(),
                size=size,
                tagline=row.get("tagline", "").strip(),
                source="csv",
            ))
    return leads


# ── Single URL ────────────────────────────────────────────────────────────────

def from_url(url: str, size: BrandSize = "small", category: str = "") -> BrandLead:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return BrandLead(url=url, size=size, category=category, source="manual")
