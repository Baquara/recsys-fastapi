from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.schemas.user import UserRatingRead, UserRatingsPayload, UserRatingsUpdatePayload
from app.repositories import user_repository

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "",
    response_model=List[UserRatingRead],
    summary="List all ratings",
    description="Returns every user–item rating record in the database.",
)
def list_ratings(db: Session = Depends(get_db)):
    return user_repository.get_all(db)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Add user ratings",
    description=(
        "Insert one or more explicit user–item ratings.\n\n"
        "- `rating` must be between 0 and 5.\n"
        "- `timestamp` is a Unix epoch integer.\n"
        "- These records are the **primary input** for collaborative filtering."
    ),
)
def create_ratings(payload: UserRatingsPayload, db: Session = Depends(get_db)):
    user_repository.create_many(db, payload.items)
    return {"detail": f"{len(payload.items)} rating(s) added successfully"}


@router.get(
    "/{user_id}",
    response_model=List[UserRatingRead],
    summary="Get ratings for a user",
    description="Fetch all rating records belonging to a specific user.",
)
def get_user_ratings(user_id: int, db: Session = Depends(get_db)):
    ratings = user_repository.get_by_user_id(db, user_id)
    if not ratings:
        raise HTTPException(status_code=404, detail=f"No ratings found for user {user_id}")
    return ratings


@router.put(
    "/{user_id}",
    summary="Update user ratings",
    description=(
        "Update `rating` and `timestamp` for one or more existing user–item pairs.\n\n"
        "- Returns **404** if a `userId` / `itemId` pair does not exist.\n"
        "- Use `POST /users` to add new ratings."
    ),
)
def update_ratings(user_id: int, payload: UserRatingsUpdatePayload, db: Session = Depends(get_db)):
    updated = []
    for entry in payload.items:
        rating = user_repository.update(db, user_id, entry.itemId, entry)
        if not rating:
            raise HTTPException(
                status_code=404,
                detail=f"Rating for user {user_id} / item {entry.itemId} not found",
            )
        updated.append(rating)
    return {"detail": f"{len(updated)} rating(s) updated"}


@router.delete(
    "/{user_id}",
    summary="Delete a user",
    description="Remove **all rating records** for a given user.",
)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    count = user_repository.delete_by_user_id(db, user_id)
    if count == 0:
        raise HTTPException(status_code=404, detail=f"No ratings found for user {user_id}")
    return {"detail": f"Deleted {count} rating(s) for user {user_id}"}
