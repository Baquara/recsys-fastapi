import os
import pytest
from app.config import Settings, _int, _float, _str, _bool


def test_defaults():
    s = Settings()
    assert s.database_url == "sqlite:///./data/db0.db"
    assert s.app_host == "0.0.0.0"
    assert s.app_port == 8000
    assert s.app_reload is False
    assert s.hybrid_threshold == 5
    assert s.hybrid_alpha == 0.5
    assert s.hybrid_pool_multiplier == 3
    assert s.collab_popularity_threshold == 1
    assert s.collab_activity_threshold == 1
    assert s.collab_max_ratings == 2_000_000
    assert s.collab_n_neighbors == 20
    assert s.content_ngram_max == 3
    assert s.content_min_df == 1
    assert s.fuzzy_match_threshold == 60
    assert s.hardware_backend == "none"


def test_security_defaults(monkeypatch):
    # Clear any vars that conftest or the environment may have set.
    for key in ("DISABLE_SECURITY", "SECRET_KEY", "JWT_ALGORITHM",
                "ACCESS_TOKEN_EXPIRE_MINUTES", "CORS_ORIGINS",
                "RATE_LIMIT_CALLS", "RATE_LIMIT_PERIOD",
                "FIRST_SUPERUSER", "FIRST_SUPERUSER_PASSWORD"):
        monkeypatch.delenv(key, raising=False)
    s = Settings()
    assert s.disable_security is False
    assert s.secret_key == "CHANGE_THIS_IN_PRODUCTION"
    assert s.jwt_algorithm == "HS256"
    assert s.access_token_expire_minutes == 30
    assert s.cors_origins == "*"
    assert s.rate_limit_calls == 100
    assert s.rate_limit_period == 60
    assert s.first_superuser == "admin"
    assert s.first_superuser_password == "changeme"


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("APP_HOST", "127.0.0.1")
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("APP_RELOAD", "true")
    monkeypatch.setenv("HYBRID_THRESHOLD", "10")
    monkeypatch.setenv("HYBRID_ALPHA", "0.7")
    monkeypatch.setenv("HYBRID_POOL_MULTIPLIER", "5")
    monkeypatch.setenv("COLLAB_POPULARITY_THRESHOLD", "3")
    monkeypatch.setenv("COLLAB_ACTIVITY_THRESHOLD", "2")
    monkeypatch.setenv("COLLAB_MAX_RATINGS", "500000")
    monkeypatch.setenv("COLLAB_N_NEIGHBORS", "15")
    monkeypatch.setenv("CONTENT_NGRAM_MAX", "2")
    monkeypatch.setenv("CONTENT_MIN_DF", "2")
    monkeypatch.setenv("FUZZY_MATCH_THRESHOLD", "80")
    monkeypatch.setenv("DISABLE_SECURITY", "true")
    monkeypatch.setenv("SECRET_KEY", "supersecret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("CORS_ORIGINS", "https://example.com,https://app.example.com")
    monkeypatch.setenv("RATE_LIMIT_CALLS", "50")
    monkeypatch.setenv("RATE_LIMIT_PERIOD", "30")
    monkeypatch.setenv("FIRST_SUPERUSER", "superadmin")
    monkeypatch.setenv("FIRST_SUPERUSER_PASSWORD", "strongpass")

    s = Settings()
    assert s.database_url == "sqlite:///./test.db"
    assert s.app_host == "127.0.0.1"
    assert s.app_port == 9000
    assert s.app_reload is True
    assert s.hybrid_threshold == 10
    assert s.hybrid_alpha == 0.7
    assert s.hybrid_pool_multiplier == 5
    assert s.collab_popularity_threshold == 3
    assert s.collab_activity_threshold == 2
    assert s.collab_max_ratings == 500_000
    assert s.collab_n_neighbors == 15
    assert s.content_ngram_max == 2
    assert s.content_min_df == 2
    assert s.fuzzy_match_threshold == 80
    assert s.disable_security is True
    assert s.secret_key == "supersecret"
    assert s.jwt_algorithm == "HS256"
    assert s.access_token_expire_minutes == 60
    assert s.cors_origins == "https://example.com,https://app.example.com"
    assert s.rate_limit_calls == 50
    assert s.rate_limit_period == 30
    assert s.first_superuser == "superadmin"
    assert s.first_superuser_password == "strongpass"


def test_int_helper(monkeypatch):
    monkeypatch.setenv("MY_INT", "42")
    assert _int("MY_INT", 0) == 42
    assert _int("MISSING_INT", 99) == 99


def test_float_helper(monkeypatch):
    monkeypatch.setenv("MY_FLOAT", "3.14")
    assert _float("MY_FLOAT", 0.0) == pytest.approx(3.14)
    assert _float("MISSING_FLOAT", 1.5) == pytest.approx(1.5)


def test_str_helper(monkeypatch):
    monkeypatch.setenv("MY_STR", "hello")
    assert _str("MY_STR", "default") == "hello"
    assert _str("MISSING_STR", "default") == "default"


@pytest.mark.parametrize("value,expected", [
    ("true", True),
    ("1", True),
    ("yes", True),
    ("false", False),
    ("0", False),
    ("no", False),
])
def test_bool_helper_values(monkeypatch, value, expected):
    monkeypatch.setenv("MY_BOOL", value)
    assert _bool("MY_BOOL", False) is expected


def test_bool_helper_default_true(monkeypatch):
    monkeypatch.delenv("MY_BOOL", raising=False)
    assert _bool("MY_BOOL", True) is True


def test_bool_helper_default_false(monkeypatch):
    monkeypatch.delenv("MY_BOOL", raising=False)
    assert _bool("MY_BOOL", False) is False
