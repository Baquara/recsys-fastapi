from typing import List
from sqlalchemy.orm import Session
from app.models.event import Event
from app.schemas.event import EventCreate


def get_all(db: Session) -> List[Event]:
    return db.query(Event).all()


def get_by_user_id(db: Session, user_id: int) -> List[Event]:
    return db.query(Event).filter(Event.userId == user_id).all()


def get_by_item_id(db: Session, item_id: int) -> List[Event]:
    return db.query(Event).filter(Event.itemId == item_id).all()


def create(db: Session, event: EventCreate) -> Event:
    db_event = Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def clear(db: Session) -> None:
    db.query(Event).delete()
    db.commit()
