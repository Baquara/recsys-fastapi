"""
Auth tests.

Most run in sandbox mode (DISABLE_SECURITY=true from conftest).
The TestRealAuth class temporarily re-enables security via monkeypatch
to exercise the real JWT flow.
"""

import pytest
from unittest.mock import patch

from app.auth import service as auth_service
from app.auth.dependencies import get_current_user, _SANDBOX_USER
from app.config import settings


# ── Sandbox mode (DISABLE_SECURITY=true) ──────────────────────────────────────

def test_sandbox_token_any_credentials(client):
    """Any credentials return a token when security is disabled."""
    r = client.post("/auth/token", data={"username": "anyone", "password": "anything"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_sandbox_endpoint_accessible_without_token(client):
    """Protected endpoints are accessible without auth in sandbox mode."""
    with patch("app.routers.recommendations.recommendation_service.get_auto") as m:
        m.return_value = {"method": "content_based", "ratings_count": 0, "items": []}
        r = client.get("/recommendations/auto?sel_item=Alpha&nrec=3")
    assert r.status_code == 200


def test_sandbox_get_current_user_returns_sandbox_sentinel(db):
    import asyncio
    user = asyncio.run(get_current_user(token=None, db=db))
    assert user is _SANDBOX_USER
    assert user.username == "sandbox"


# ── Real JWT auth (DISABLE_SECURITY=false) ────────────────────────────────────

class TestRealAuth:
    @pytest.fixture(autouse=True)
    def enable_security(self, monkeypatch):
        monkeypatch.setattr(settings, "disable_security", False)

    @pytest.fixture
    def admin(self, db):
        user = auth_service.create_user(
            db, settings.first_superuser, settings.first_superuser_password
        )
        db.commit()
        return user

    # ── login ──────────────────────────────────────────────────────────────────

    def test_login_success(self, client, admin):
        r = client.post("/auth/token", data={
            "username": settings.first_superuser,
            "password": settings.first_superuser_password,
        })
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client, admin):
        r = client.post("/auth/token", data={
            "username": settings.first_superuser,
            "password": "wrong",
        })
        assert r.status_code == 401

    def test_login_unknown_user(self, client):
        r = client.post("/auth/token", data={"username": "ghost", "password": "x"})
        assert r.status_code == 401

    # ── protected routes ───────────────────────────────────────────────────────

    def test_no_token_returns_401(self, client):
        r = client.get("/items")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self, client):
        r = client.get("/items", headers={"Authorization": "Bearer bad.token.here"})
        assert r.status_code == 401

    def test_token_with_missing_sub_returns_401(self, client):
        # Craft a token without the 'sub' claim
        token = auth_service.create_access_token({})
        r = client.get("/items", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

    def test_valid_token_grants_access(self, client, admin):
        token_r = client.post("/auth/token", data={
            "username": settings.first_superuser,
            "password": settings.first_superuser_password,
        })
        token = token_r.json()["access_token"]
        r = client.get("/items", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_inactive_user_rejected(self, client, db, admin):
        admin.is_active = False
        db.commit()
        token = auth_service.create_access_token({"sub": admin.username})
        r = client.get("/items", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

    def test_nonexistent_sub_returns_401(self, client):
        # Token references a username that doesn't exist in DB
        token = auth_service.create_access_token({"sub": "nobody"})
        r = client.get("/items", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401


# ── auth/service unit tests ───────────────────────────────────────────────────

def test_hash_and_verify_password():
    hashed = auth_service.hash_password("secret123")
    assert auth_service.verify_password("secret123", hashed)
    assert not auth_service.verify_password("wrong", hashed)


def test_create_and_get_user(db):
    auth_service.create_user(db, "alice", "pass")
    db.commit()
    user = auth_service.get_user(db, "alice")
    assert user is not None
    assert user.username == "alice"


def test_get_user_not_found(db):
    assert auth_service.get_user(db, "nobody") is None


def test_authenticate_user_success(db):
    auth_service.create_user(db, "bob", "pw")
    db.commit()
    user = auth_service.authenticate_user(db, "bob", "pw")
    assert user is not None


def test_authenticate_user_wrong_password(db):
    auth_service.create_user(db, "carol", "pw")
    db.commit()
    assert auth_service.authenticate_user(db, "carol", "wrong") is None


def test_authenticate_user_unknown(db):
    assert auth_service.authenticate_user(db, "ghost", "pw") is None


def test_create_access_token_contains_sub():
    from jose import jwt as jose_jwt
    token = auth_service.create_access_token({"sub": "testuser"})
    payload = jose_jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm]
    )
    assert payload["sub"] == "testuser"
    assert "exp" in payload


# ── _seed_superuser first-boot branch ────────────────────────────────────────

def test_seed_superuser_creates_user_when_absent():
    """Covers the create_user branch in main._seed_superuser()."""
    from unittest.mock import MagicMock, patch
    from app.main import _seed_superuser

    mock_db = MagicMock()
    with (
        patch("app.main.SessionLocal", return_value=mock_db),
        patch("app.main.auth_service.get_user", return_value=None) as mock_get,
        patch("app.main.auth_service.create_user") as mock_create,
    ):
        _seed_superuser()

    mock_get.assert_called_once_with(mock_db, settings.first_superuser)
    mock_create.assert_called_once_with(
        mock_db, settings.first_superuser, settings.first_superuser_password
    )
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()


def test_seed_superuser_skips_create_when_user_exists():
    """When admin already exists, create_user is NOT called."""
    from unittest.mock import MagicMock, patch
    from app.main import _seed_superuser

    mock_db = MagicMock()
    existing_user = MagicMock()
    with (
        patch("app.main.SessionLocal", return_value=mock_db),
        patch("app.main.auth_service.get_user", return_value=existing_user),
        patch("app.main.auth_service.create_user") as mock_create,
    ):
        _seed_superuser()

    mock_create.assert_not_called()
    mock_db.close.assert_called_once()
