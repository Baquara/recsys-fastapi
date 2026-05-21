import json
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


def get_all(db: Session) -> List[Item]:
    return db.query(Item).all()


def get_by_id(db: Session, item_id: int) -> Optional[Item]:
    return db.query(Item).filter(Item.itemId == item_id).first()


def create_many(db: Session, items: List[ItemCreate]) -> None:
    db.add_all([
        Item(
            itemId=item.itemId,
            title=item.title,
            description=item.description,
            tag=json.dumps(item.tag),
        )
        for item in items
    ])
    db.commit()


def update(db: Session, item_id: int, data: ItemUpdate) -> Optional[Item]:
    item = get_by_id(db, item_id)
    if not item:
        return None
    item.title = data.title
    item.description = data.description
    item.tag = json.dumps(data.tag)
    db.commit()
    db.refresh(item)
    return item


def delete(db: Session, item_id: int) -> Optional[Item]:
    item = get_by_id(db, item_id)
    if not item:
        return None
    db.delete(item)
    db.commit()
    return item


def clear(db: Session) -> None:
    db.query(Item).delete()
    db.commit()
