"""QA Agent — tests the live API, checks health, reports issues."""
from __future__ import annotations

from .base_agent import run_agent

BASE_URL = "https://adreel.studio"

SYSTEM = f"""You are a QA Engineer for adreel.studio, an AI video ad creation platform.

Live service: {BASE_URL}
API base: {BASE_URL}/api

Your job:
1. Test the live API endpoints and UI flows
2. Check service health
3. Write clear bug reports with reproduction steps
4. Regression-test after deployments

Key flows to test:
1. Health: GET /api/settings → should return JSON with *_set fields
2. Changelog: GET /api/changelog → should return array of entries
3. Scrape: POST /api/scrape with URL → should return product data
4. Project creation: POST /api/projects
5. Auth: GET /auth/google → should redirect to Google

When writing bug reports use this format:
## Bug: <title>
**Severity**: P0/P1/P2/P3
**Steps to reproduce**:
1. ...
**Expected**: ...
**Actual**: ...
**Evidence**: (HTTP status, response body excerpt)

Focus on facts — what the server actually returned, not speculation.
"""

ALLOWED_TOOLS = [
    "http_get",
    "http_post",
    "get_cloud_run_status",
    "get_cloud_run_logs",
    "read_file",
    "grep_code",
]


def health_check() -> str:
    """Run a full health check of the live service."""
    task = f"""Run a comprehensive health check of {BASE_URL}.

Test the following endpoints and report status for each:
1. GET {BASE_URL}/api/settings — should return JSON
2. GET {BASE_URL}/api/changelog — should return array with at least 1 entry
3. GET {BASE_URL}/ — should return 200 HTML (landing page)
4. GET {BASE_URL}/app — should return 200 HTML (app)
5. GET {BASE_URL}/auth/google — should return 302 to accounts.google.com

Also:
6. Check Cloud Run status
7. Check last 20 log lines for errors

Write a health report: 🟢 PASS / 🔴 FAIL for each check, with evidence.
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def test_scrape(url: str) -> str:
    """Test the product scraping flow."""
    task = f"""Test the product scraping endpoint with this URL: {url}

1. POST {BASE_URL}/api/scrape with body {{"url": "{url}"}}
2. Verify the response has: product_name, image_url (or image_path), price
3. Check if there are any errors in Cloud Run logs
4. Write a test report
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def regression_test() -> str:
    """Run a full regression test suite after deployment."""
    task = f"""Run a full regression test of {BASE_URL} after deployment.

Test matrix:
1. Landing page loads (GET /)
2. App page loads (GET /app)
3. Settings API returns expected shape (GET /api/settings)
4. Changelog has entries (GET /api/changelog)
5. Demo videos serve correctly (GET /demos/demo1.mp4 — check 200 or 404)
6. Auth redirect works (GET /auth/google → 302)
7. Cloud Run is healthy (check status, last 30 log lines)
8. No 5xx errors in recent logs

Output a pass/fail table and any issues found.
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)


def report_bug(observed_issue: str) -> str:
    """Investigate and write a formal bug report for an observed issue."""
    task = f"""Investigate this issue and write a formal bug report:

{observed_issue}

1. Try to reproduce it by making HTTP requests
2. Check Cloud Run logs for errors
3. Read relevant source code to understand expected behavior
4. Write a formal bug report with severity, reproduction steps, and evidence
"""
    return run_agent(SYSTEM, task, ALLOWED_TOOLS)
