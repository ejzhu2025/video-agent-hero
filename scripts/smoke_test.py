#!/usr/bin/env python3
"""
Smoke test for adreel.studio.
Usage: python scripts/smoke_test.py <base_url>
Exit code 0 = all pass, 1 = any failure.
"""
import sys
import json
import httpx

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://adreel.studio"
IS_PROD = "adreel.studio" in BASE_URL


def check(label: str, method: str, path: str, expected_status: int,
          json_body=None, assert_fn=None, headers=None) -> bool:
    url = BASE_URL + path
    try:
        r = httpx.request(
            method, url,
            json=json_body,
            headers=headers or {},
            timeout=20,
            follow_redirects=False,
        )
        status_ok = r.status_code == expected_status
        extra_ok = assert_fn(r) if assert_fn else True
        ok = status_ok and extra_ok
        icon = "✓" if ok else "✗"
        detail = "" if ok else f"  ← got {r.status_code}, expected {expected_status}"
        print(f"  {icon} {label}{detail}")
        return ok
    except Exception as e:
        print(f"  ✗ {label} — ERROR: {e}")
        return False


def main():
    print(f"\nSmoke test → {BASE_URL}\n")
    results = []

    # Core pages
    results.append(check(
        "GET /  → 200 HTML",
        "GET", "/", 200,
        assert_fn=lambda r: "text/html" in r.headers.get("content-type", ""),
    ))
    results.append(check(
        "GET /app  → 200 HTML",
        "GET", "/app", 200,
        assert_fn=lambda r: "text/html" in r.headers.get("content-type", ""),
    ))

    # API health
    results.append(check(
        "GET /api/settings  → 200 JSON with expected keys",
        "GET", "/api/settings", 200,
        assert_fn=lambda r: "anthropic_api_key_set" in r.text and "fal_key_set" in r.text,
    ))
    results.append(check(
        "GET /api/changelog  → 200 JSON array",
        "GET", "/api/changelog", 200,
        assert_fn=lambda r: isinstance(r.json(), list),
    ))

    # Auth redirect (only if Google credentials are configured)
    auth_r = httpx.get(BASE_URL + "/auth/google", follow_redirects=False, timeout=10)
    if auth_r.status_code == 404:
        print("  ⚠  GET /auth/google → 404 (Google credentials not set on this instance — skip)")
    else:
        ok = auth_r.status_code == 302 and "accounts.google.com" in auth_r.headers.get("location", "")
        results.append(ok)
        icon = "✓" if ok else "✗"
        print(f"  {icon} GET /auth/google  → 302 to Google")

    # HSTS header (only meaningful on prod over real HTTPS)
    if IS_PROD:
        results.append(check(
            "HSTS header present",
            "GET", "/", 200,
            assert_fn=lambda r: "max-age=" in r.headers.get("strict-transport-security", ""),
        ))

    passed = sum(results)
    total = len(results)
    print(f"\n{'='*40}")
    print(f"  {passed}/{total} checks passed")
    if passed < total:
        print(f"  ✗ FAILED — {total - passed} check(s) did not pass")
        print()
        sys.exit(1)
    else:
        print(f"  ✓ All checks passed")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
