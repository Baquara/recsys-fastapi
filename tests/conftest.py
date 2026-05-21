import os

# Must be set before any app module is imported so Settings() picks it up.
os.environ.setdefault("DISABLE_SECURITY", "true")

import json
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
import app.middleware as _mw

# ── Shared in-memory engine ───────────────────────────────────────────────────

_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=_ENGINE)
_Session = sessionmaker(bind=_ENGINE)


def _override_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_tables():
    """Wipe every table before each test for full isolation."""
    db = _Session()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()
    # Also reset the rate-limiter sliding window between tests.
    _mw._rate_limit_store.clear()


@pytest.fixture
def db():
    session = _Session()
    yield session
    session.close()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def rec_engine():
    """
    Separate in-memory engine for recommender unit tests.
    Pre-populated with enough items and ratings to exercise all algorithms.
    Item 7 has 0 ratings (cold-start), item 8 has 3 (hybrid), items 1-6 have 6 (collaborative).
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE items (itemId INT, title TEXT, description TEXT, tag TEXT)"
        ))
        conn.execute(text(
            "CREATE TABLE users (userId INTEGER, itemId INTEGER, rating REAL, timestamp INTEGER)"
        ))

    items = [
        (1, "Alpha",   "A beautiful nature scene with mountains and rivers", '["nature","mountains"]'),
        (2, "Beta",    "A wonderful beach with ocean waves and sand dunes",  '["nature","beach","ocean"]'),
        (3, "Gamma",   "A modern tech gadget for everyday computing tasks",  '["tech","gadget","computing"]'),
        (4, "Delta",   "A wildlife documentary about endangered animals",     '["nature","wildlife","animals"]'),
        (5, "Epsilon", "A science fiction film about deep space exploration", '["sci-fi","space","movies"]'),
        (6, "Zeta",    "A historical account of ancient civilizations",       '["history","documentary"]'),
        (7, "Eta",     "A brand new item with no ratings yet",                '["new"]'),
        (8, "Theta",   "An item with only a few ratings so far",              '["few","ratings"]'),
    ]
    ratings = [
        # items 1-6 each get 6 ratings from users 1-6
        *[(u, i, float(5 - (u + i) % 3), 1000 + u * 10 + i) for u in range(1, 7) for i in range(1, 7)],
        # item 8 gets 3 ratings
        (1, 8, 4.0, 2001),
        (2, 8, 3.5, 2002),
        (3, 8, 5.0, 2003),
    ]
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO items VALUES (:itemId, :title, :description, :tag)"),
            [{"itemId": r[0], "title": r[1], "description": r[2], "tag": r[3]} for r in items],
        )
        conn.execute(
            text("INSERT INTO users VALUES (:userId, :itemId, :rating, :timestamp)"),
            [{"userId": r[0], "itemId": r[1], "rating": r[2], "timestamp": r[3]} for r in ratings],
        )
    return engine
