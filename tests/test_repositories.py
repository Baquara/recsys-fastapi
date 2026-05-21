import json
import pytest
from app.repositories import item_repository, user_repository, event_repository
from app.schemas.item import ItemCreate, ItemUpdate
from app.schemas.user import UserRatingCreate, UserRatingUpdate
from app.schemas.event import EventCreate


# ── Item repository ───────────────────────────────────────────────────────────

def test_item_get_all_empty(db):
    assert item_repository.get_all(db) == []


def test_item_create_and_get_all(db):
    item_repository.create_many(db, [
        ItemCreate(itemId=1, title="Alpha", description="Desc", tag=["a"]),
        ItemCreate(itemId=2, title="Beta",  description="Desc", tag=["b"]),
    ])
    items = item_repository.get_all(db)
    assert len(items) == 2


def test_item_get_by_id_found(db):
    item_repository.create_many(db, [ItemCreate(itemId=5, title="X", description="D", tag=[])])
    item = item_repository.get_by_id(db, 5)
    assert item is not None
    assert item.title == "X"


def test_item_get_by_id_not_found(db):
    assert item_repository.get_by_id(db, 999) is None


def test_item_update_found(db):
    item_repository.create_many(db, [ItemCreate(itemId=1, title="Old", description="D", tag=[])])
    updated = item_repository.update(db, 1, ItemUpdate(title="New", description="D2", tag=["x"]))
    assert updated.title == "New"
    assert json.loads(updated.tag) == ["x"]


def test_item_update_not_found(db):
    assert item_repository.update(db, 999, ItemUpdate(title="X", description="D", tag=[])) is None


def test_item_delete_found(db):
    item_repository.create_many(db, [ItemCreate(itemId=1, title="X", description="D", tag=[])])
    deleted = item_repository.delete(db, 1)
    assert deleted is not None
    assert item_repository.get_by_id(db, 1) is None


def test_item_delete_not_found(db):
    assert item_repository.delete(db, 999) is None


def test_item_clear(db):
    item_repository.create_many(db, [ItemCreate(itemId=1, title="X", description="D", tag=[])])
    item_repository.clear(db)
    assert item_repository.get_all(db) == []


# ── User repository ───────────────────────────────────────────────────────────

def test_user_get_all_empty(db):
    assert user_repository.get_all(db) == []


def test_user_create_and_get_all(db):
    user_repository.create_many(db, [
        UserRatingCreate(userId=1, itemId=1, rating=5.0, timestamp=1000),
        UserRatingCreate(userId=1, itemId=2, rating=4.0, timestamp=1001),
    ])
    assert len(user_repository.get_all(db)) == 2


def test_user_get_by_user_id(db):
    user_repository.create_many(db, [
        UserRatingCreate(userId=1, itemId=1, rating=5.0, timestamp=1000),
        UserRatingCreate(userId=2, itemId=1, rating=3.0, timestamp=1001),
    ])
    ratings = user_repository.get_by_user_id(db, 1)
    assert len(ratings) == 1
    assert ratings[0].userId == 1


def test_user_get_by_user_and_item(db):
    user_repository.create_many(db, [UserRatingCreate(userId=1, itemId=2, rating=4.0, timestamp=1000)])
    rating = user_repository.get_by_user_and_item(db, 1, 2)
    assert rating is not None
    assert rating.rating == 4.0


def test_user_get_by_user_and_item_not_found(db):
    assert user_repository.get_by_user_and_item(db, 99, 99) is None


def test_user_update_found(db):
    user_repository.create_many(db, [UserRatingCreate(userId=1, itemId=1, rating=3.0, timestamp=1000)])
    updated = user_repository.update(db, 1, 1, UserRatingUpdate(itemId=1, rating=5.0, timestamp=2000))
    assert updated.rating == 5.0


def test_user_update_not_found(db):
    result = user_repository.update(db, 99, 99, UserRatingUpdate(itemId=99, rating=1.0, timestamp=1))
    assert result is None


def test_user_delete_by_user_id(db):
    user_repository.create_many(db, [
        UserRatingCreate(userId=1, itemId=1, rating=5.0, timestamp=1000),
        UserRatingCreate(userId=1, itemId=2, rating=4.0, timestamp=1001),
    ])
    count = user_repository.delete_by_user_id(db, 1)
    assert count == 2
    assert user_repository.get_by_user_id(db, 1) == []


def test_user_clear(db):
    user_repository.create_many(db, [UserRatingCreate(userId=1, itemId=1, rating=5.0, timestamp=1000)])
    user_repository.clear(db)
    assert user_repository.get_all(db) == []


# ── Event repository ──────────────────────────────────────────────────────────

def test_event_get_all_empty(db):
    assert event_repository.get_all(db) == []


def test_event_create_and_get_all(db):
    event_repository.create(db, EventCreate(userId=1, itemId=1, rating=1.0, timestamp=1000))
    assert len(event_repository.get_all(db)) == 1


def test_event_get_by_user_id(db):
    event_repository.create(db, EventCreate(userId=1, itemId=1, rating=1.0, timestamp=1000))
    event_repository.create(db, EventCreate(userId=2, itemId=1, rating=1.0, timestamp=1001))
    assert len(event_repository.get_by_user_id(db, 1)) == 1


def test_event_get_by_item_id(db):
    event_repository.create(db, EventCreate(userId=1, itemId=5, rating=1.0, timestamp=1000))
    event_repository.create(db, EventCreate(userId=1, itemId=6, rating=1.0, timestamp=1001))
    assert len(event_repository.get_by_item_id(db, 5)) == 1


def test_event_clear(db):
    event_repository.create(db, EventCreate(userId=1, itemId=1, rating=1.0, timestamp=1000))
    event_repository.clear(db)
    assert event_repository.get_all(db) == []
