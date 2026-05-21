from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.schemas.event import EventCreate, EventRead
from app.repositories import event_repository

router = APIRouter(
    prefix="/events",
    tags=["Events"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "",
    response_model=List[EventRead],
    summary="List events",
    description=(
        "Returns event records, optionally filtered by `user_id` or `item_id`.\n\n"
        "- Omit both query params to fetch all events.\n"
        "- Pass `user_id` to get events for a specific user.\n"
        "- Pass `item_id` to get events for a specific item."
    ),
)
def list_events(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    item_id: Optional[int] = Query(None, description="Filter by item ID"),
    db: Session = Depends(get_db),
):
    if user_id is not None:
        return event_repository.get_by_user_id(db, user_id)
    if item_id is not None:
        return event_repository.get_by_item_id(db, item_id)
    return event_repository.get_all(db)


@router.post(
    "",
    response_model=EventRead,
    summary="Record an implicit feedback event",
    description=(
        "Log a single implicit feedback event (click, view, purchase, etc.).\n\n"
        "Events are stored in a separate `events` table, keeping implicit and explicit signals distinct. "
        "Use `rating` as an implicit signal strength (e.g. `1.0` = clicked, `5.0` = purchased)."
    ),
)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    return event_repository.create(db, event)
