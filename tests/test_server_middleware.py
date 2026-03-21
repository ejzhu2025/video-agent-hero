"""Regression tests for web/server.py middleware.

Covers:
- HTTP→HTTPS redirect (301, preserves method)
- HSTS header on HTTPS responses
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    """TestClient with middleware wired up, no startup side effects."""
    from unittest.mock import patch, MagicMock
    import sys

    # Stub heavy imports before loading server
    sys.modules.setdefault("agent.deps", MagicMock())
    sys.modules.setdefault("web.templates", MagicMock(_HTML="<html/>"))
    sys.modules.setdefault("web.landing", MagicMock(_LANDING_HTML="<html/>"))

    with patch("web.server.deps") as mock_deps, \
         patch("web.server._HTML", "<html/>"), \
         patch("web.server._LANDING_HTML", "<html/>"):
        mock_deps.init.return_value = None
        mock_deps.emit.return_value = None

        from web.server import app
        return TestClient(app, raise_server_exceptions=False)


class TestHttpsRedirect:
    def test_http_request_redirects_to_https(self, client):
        """X-Forwarded-Proto: http must trigger a 301 redirect to https."""
        r = client.get(
            "/api/settings",
            headers={"x-forwarded-proto": "http"},
            follow_redirects=False,
        )
        assert r.status_code == 301
        assert r.headers["location"].startswith("https://")

    def test_https_request_not_redirected(self, client):
        """X-Forwarded-Proto: https must pass through normally."""
        r = client.get(
            "/api/settings",
            headers={"x-forwarded-proto": "https"},
            follow_redirects=False,
        )
        # Should NOT be a redirect
        assert r.status_code != 301
        assert r.status_code != 302

    def test_redirect_is_301_not_302(self, client):
        """Must be 301 (preserves POST method), not 302 (converts to GET)."""
        r = client.post(
            "/api/settings",
            headers={"x-forwarded-proto": "http"},
            json={},
            follow_redirects=False,
        )
        assert r.status_code == 301, (
            "HTTP→HTTPS redirect must be 301 to preserve POST method. "
            "302 would convert POST to GET, breaking Approve & Generate."
        )

    def test_redirect_preserves_path(self, client):
        """Redirect must keep the full request path."""
        r = client.get(
            "/api/changelog",
            headers={"x-forwarded-proto": "http"},
            follow_redirects=False,
        )
        assert r.status_code == 301
        assert "/api/changelog" in r.headers["location"]


class TestHSTS:
    def test_hsts_header_on_https_response(self, client):
        """HTTPS responses must include Strict-Transport-Security header."""
        r = client.get(
            "/api/settings",
            headers={"x-forwarded-proto": "https"},
        )
        hsts = r.headers.get("strict-transport-security", "")
        assert "max-age=" in hsts, f"HSTS header missing or malformed: {hsts!r}"

    def test_hsts_max_age_at_least_1_year(self, client):
        """HSTS max-age must be at least 1 year (31536000 seconds)."""
        r = client.get(
            "/",
            headers={"x-forwarded-proto": "https"},
        )
        hsts = r.headers.get("strict-transport-security", "")
        max_age = 0
        for part in hsts.split(";"):
            part = part.strip()
            if part.startswith("max-age="):
                max_age = int(part.split("=")[1])
        assert max_age >= 31_536_000, f"HSTS max-age too short: {max_age}"
