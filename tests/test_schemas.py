import json
import pytest
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate, ItemBatchCreate
from app.schemas.user import UserRatingCreate, UserRatingRead, UserRatingUpdate, UserRatingsPayload, UserRatingsUpdatePayload
from app.schemas.event import EventCreate, EventRead
from app.schemas.recommendation import CollaborativeResult, ContentBasedResult, SystemInfo


# ── Item schemas ──────────────────────────────────────────────────────────────

def test_item_create():
    item = ItemCreate(itemId=1, title="T", description="D", tag=["a", "b"])
    assert item.itemId == 1
    assert item.tag == ["a", "b"]


def test_item_read_parses_tag_from_string():
    item = ItemRead(itemId=1, title="T", description="D", tag='["x","y"]')
    assert item.tag == ["x", "y"]


def test_item_read_accepts_tag_as_list():
    item = ItemRead(itemId=1, title="T", description="D", tag=["x", "y"])
    assert item.tag == ["x", "y"]


def test_item_update():
    upd = ItemUpdate(title="New", description="Desc", tag=["z"])
    assert upd.title == "New"


def test_item_batch_create():
    payload = ItemBatchCreate(items=[
        ItemCreate(itemId=1, title="T", description="D", tag=["a"]),
    ])
    assert len(payload.items) == 1


# ── User schemas ──────────────────────────────────────────────────────────────

def test_user_rating_create():
    r = UserRatingCreate(userId=1, itemId=2, rating=4.5, timestamp=1000)
    assert r.rating == 4.5


def test_user_rating_create_bounds():
    with pytest.raises(Exception):
        UserRatingCreate(userId=1, itemId=2, rating=6.0, timestamp=1000)
    with pytest.raises(Exception):
        UserRatingCreate(userId=1, itemId=2, rating=-1.0, timestamp=1000)


def test_user_rating_read():
    r = UserRatingRead(userId=1, itemId=2, rating=3.0, timestamp=999)
    assert r.userId == 1


def test_user_rating_update():
    u = UserRatingUpdate(itemId=2, rating=3.0, timestamp=999)
    assert u.itemId == 2


def test_user_ratings_payload():
    p = UserRatingsPayload(items=[
        UserRatingCreate(userId=1, itemId=1, rating=5.0, timestamp=1000)
    ])
    assert len(p.items) == 1


def test_user_ratings_update_payload():
    p = UserRatingsUpdatePayload(items=[
        UserRatingUpdate(itemId=1, rating=4.0, timestamp=1000)
    ])
    assert len(p.items) == 1


# ── Event schemas ─────────────────────────────────────────────────────────────

def test_event_create():
    e = EventCreate(userId=1, itemId=2, rating=1.0, timestamp=1000)
    assert e.rating == 1.0


def test_event_read():
    e = EventRead(id=1, userId=1, itemId=2, rating=1.0, timestamp=1000)
    assert e.id == 1


# ── Recommendation schemas ────────────────────────────────────────────────────

def test_collaborative_result():
    r = CollaborativeResult(
        execution_time={"total": 0.1, "data_processing": 0.05, "recommendation": 0.05},
        recommendations=[{"title": "X", "rank": 1, "distance": 0.2}],
    )
    assert r.recommendations[0]["title"] == "X"


def test_content_based_result():
    r = ContentBasedResult(item_index=0, api_exec_time="0.01", items=[{"name": "Y"}])
    assert r.item_index == 0


def test_system_info():
    s = SystemInfo(
        uptime="1 day",
        total_ram_mb="8192",
        available_ram_mb="4096",
        cpu_model="Intel",
        cpu_clock_mhz="3600",
        database_size="1M",
    )
    assert s.uptime == "1 day"
