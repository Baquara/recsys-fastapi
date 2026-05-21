import pytest
from app.config import settings
import app.middleware as mw


# ── Security headers ───────────────────────────────────────────────────────────

def test_security_headers_on_200(client):
    r = client.get("/items")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "strict-origin-when-cross-origin" in r.headers["Referrer-Policy"]
    assert "geolocation=()" in r.headers["Permissions-Policy"]


def test_security_headers_on_404(client):
    r = client.get("/items/999999")
    assert r.headers["X-Content-Type-Options"] == "nosniff"


# ── Rate limiter — sandbox bypassed ───────────────────────────────────────────

def test_rate_limit_not_applied_in_sandbox_mode(client):
    """With DISABLE_SECURITY=true the rate limiter is skipped entirely."""
    for _ in range(20):
        r = client.get("/items")
    assert r.status_code == 200  # never 429


# ── Rate limiter — security enabled ───────────────────────────────────────────

def test_rate_limit_allows_requests_under_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "disable_security", False)
    monkeypatch.setattr(settings, "rate_limit_calls", 5)
    monkeypatch.setattr(settings, "rate_limit_period", 60)
    mw._rate_limit_store.clear()

    for _ in range(5):
        r = client.get("/items")  # returns 401 (no auth) but rate limiter still counts it
    assert r.status_code != 429


def test_rate_limit_blocks_when_exceeded(client, monkeypatch):
    monkeypatch.setattr(settings, "disable_security", False)
    monkeypatch.setattr(settings, "rate_limit_calls", 2)
    monkeypatch.setattr(settings, "rate_limit_period", 60)
    mw._rate_limit_store.clear()

    client.get("/items")  # request 1
    client.get("/items")  # request 2
    r = client.get("/items")  # request 3 — should be 429
    assert r.status_code == 429
    assert "detail" in r.json()
    assert "Retry-After" in r.headers


def test_rate_limit_retry_after_header(client, monkeypatch):
    monkeypatch.setattr(settings, "disable_security", False)
    monkeypatch.setattr(settings, "rate_limit_calls", 1)
    monkeypatch.setattr(settings, "rate_limit_period", 120)
    mw._rate_limit_store.clear()

    client.get("/items")
    r = client.get("/items")
    assert r.status_code == 429
    assert r.headers["Retry-After"] == "120"


def test_rate_limit_evicts_expired_timestamps(client, monkeypatch):
    """Timestamps older than the window period are evicted and don't count."""
    import time
    monkeypatch.setattr(settings, "disable_security", False)
    monkeypatch.setattr(settings, "rate_limit_calls", 1)
    monkeypatch.setattr(settings, "rate_limit_period", 1)
    mw._rate_limit_store.clear()

    # Pre-populate with a timestamp 10 seconds in the past (outside any 1s window)
    from collections import deque
    mw._rate_limit_store["testclient"] = deque([time.monotonic() - 10])

    # The expired entry is evicted → window is effectively empty → request passes
    r = client.get("/items")
    assert r.status_code != 429  # 401 (no auth) or 200, not 429
