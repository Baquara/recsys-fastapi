from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.item import ItemBatchCreate, ItemRead, ItemUpdate
from app.repositories import item_repository

router = APIRouter(prefix="/items", tags=["Items"])


@router.get(
    "",
    response_model=List[ItemRead],
    summary="List all items",
    description="Returns every item currently stored in the catalogue.",
)
def list_items(db: Session = Depends(get_db)):
    return item_repository.get_all(db)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Add items to the catalogue",
    description=(
        "Insert one or more items in a single request.\n\n"
        "- `itemId` must be unique — duplicate IDs will raise a DB error.\n"
        "- `description` + `tag` are combined as TF-IDF input for the content-based recommender.\n"
        "- Use `PUT /items/{item_id}` to update existing items."
    ),
)
def create_items(payload: ItemBatchCreate, db: Session = Depends(get_db)):
    item_repository.create_many(db, payload.items)
    return {"detail": f"{len(payload.items)} item(s) added successfully"}


@router.get(
    "/{item_id}",
    response_model=ItemRead,
    summary="Get a single item",
    description="Fetch a catalogue item by its `item_id`. Returns 404 if not found.",
)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = item_repository.get_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return item


@router.put(
    "/{item_id}",
    response_model=ItemRead,
    summary="Update an item",
    description=(
        "Replace the `title`, `description`, and `tag` of an existing item.\n\n"
        "- Returns **404** if no item with `item_id` exists.\n"
        "- `itemId` itself is immutable; create a new item and delete the old one to change it."
    ),
)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)):
    item = item_repository.update(db, item_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return item


@router.delete(
    "/{item_id}",
    summary="Delete an item",
    description=(
        "Remove an item from the catalogue by its `item_id`.\n\n"
        "> Associated ratings or events referencing this `itemId` are **not** automatically removed."
    ),
)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = item_repository.delete(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return {"detail": f"Item {item_id} deleted"}
