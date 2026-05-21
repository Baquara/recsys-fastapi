from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import UserRating
from app.schemas.user import UserRatingCreate, UserRatingUpdate


def get_all(db: Session) -> List[UserRating]:
    return db.query(UserRating).all()


def get_by_user_id(db: Session, user_id: int) -> List[UserRating]:
    return db.query(UserRating).filter(UserRating.userId == user_id).all()


def get_by_user_and_item(db: Session, user_id: int, item_id: int) -> Optional[UserRating]:
    return db.query(UserRating).filter(
        UserRating.userId == user_id,
        UserRating.itemId == item_id,
    ).first()


def create_many(db: Session, ratings: List[UserRatingCreate]) -> None:
    db.add_all([
        UserRating(
            userId=r.userId,
            itemId=r.itemId,
            rating=r.rating,
            timestamp=r.timestamp,
        )
        for r in ratings
    ])
    db.commit()


def update(db: Session, user_id: int, item_id: int, data: UserRatingUpdate) -> Optional[UserRating]:
    rating = get_by_user_and_item(db, user_id, item_id)
    if not rating:
        return None
    rating.rating = data.rating
    rating.timestamp = data.timestamp
    db.commit()
    db.refresh(rating)
    return rating


def delete_by_user_id(db: Session, user_id: int) -> int:
    count = db.query(UserRating).filter(UserRating.userId == user_id).delete()
    db.commit()
    return count


def clear(db: Session) -> None:
    db.query(UserRating).delete()
    db.commit()
