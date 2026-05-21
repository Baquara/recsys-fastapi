from fastapi import FastAPI, Request, HTTPException, Query
from sqlalchemy import create_engine, inspect, text
from typing import Optional, List, Dict, Any
import os
import json
import pandas as pd
import collaborative_filtering_rec
import content_based_rec
import subprocess
from starlette.responses import JSONResponse
from pydantic import BaseModel, Field


# ── Pydantic models ───────────────────────────────────────────────────────────

class Item(BaseModel):
    itemId: str = Field(..., example="item_42", description="Unique identifier for the item")
    title: str = Field(..., example="Inception", description="Display name shown to users")
    description: str = Field(
        ...,
        example="A mind-bending thriller about dreams within dreams.",
        description="Full-text description used by the content-based recommender to compute TF-IDF similarity",
    )
    tag: List[str] = Field(
        ...,
        example=["sci-fi", "thriller", "christopher-nolan"],
        description="Labels/genres used alongside the description for content similarity scoring",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "itemId": "item_42",
                "title": "Inception",
                "description": "A mind-bending thriller about dreams within dreams.",
                "tag": ["sci-fi", "thriller", "christopher-nolan"],
            }
        }


class ItemList(BaseModel):
    items: List[Item] = Field(..., description="Batch of items to insert into the catalogue")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "itemId": "item_42",
                        "title": "Inception",
                        "description": "A mind-bending thriller about dreams within dreams.",
                        "tag": ["sci-fi", "thriller"],
                    },
                    {
                        "itemId": "item_43",
                        "title": "The Matrix",
                        "description": "A hacker discovers reality is a simulation.",
                        "tag": ["sci-fi", "action", "cyberpunk"],
                    },
                ]
            }
        }


# ── Tag metadata (Swagger sections) ──────────────────────────────────────────

tags_metadata = [
    {
        "name": "Items",
        "description": (
            "Manage the **item catalogue** — the entities being recommended "
            "(movies, products, articles, etc.). "
            "Item `description` and `tag` fields power the content-based recommender."
        ),
    },
    {
        "name": "Users",
        "description": (
            "Manage **explicit user–item ratings**. "
            "Each record links a `userId` to an `itemId` with a numeric score (0–5) and a timestamp. "
            "These ratings are the input for the collaborative filtering engine."
        ),
    },
    {
        "name": "Events",
        "description": (
            "Track **implicit feedback** events such as clicks, views, or purchases, "
            "stored separately from explicit ratings. "
            "Useful for building hybrid recommenders."
        ),
    },
    {
        "name": "Recommendations",
        "description": (
            "Core recommendation endpoints.\n\n"
            "| Endpoint | Algorithm | Best for |\n"
            "|---|---|---|\n"
            "| `GET /user/recommendations` | KNN collaborative filtering (cosine) | Rich rating history |\n"
            "| `GET /item/neighbors` | TF-IDF content-based (cosine) | Cold-start / new items |"
        ),
    },
    {
        "name": "Database",
        "description": "Utility endpoints for **database maintenance** (e.g. resetting a test environment).",
    },
    {
        "name": "System",
        "description": "Server **health and resource diagnostics** (RAM, CPU, uptime, DB size).",
    },
]


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Recommender System API",
    version="1.0.0",
    description="""
A **general-purpose recommender system** built with FastAPI and SQLite.

## Algorithms

| Endpoint | Algorithm | When to use |
|---|---|---|
| `GET /user/recommendations` | Collaborative Filtering — KNN with cosine similarity on the user–item matrix | Enough rating history exists |
| `GET /item/neighbors` | Content-Based — TF-IDF cosine similarity on `description` + `tag` fields | Cold-start or sparse ratings |

## Typical workflow

1. **Load catalogue** — `POST /item` with your items.
2. **Load ratings** — `POST /user` with historical user–item scores.
3. **Get recommendations** — `GET /user/recommendations?sel_item=Inception&nrec=10`.

> **Tip:** `sel_item` uses fuzzy matching, so partial or approximate titles are accepted.
""",
    openapi_tags=tags_metadata,
    contact={"name": "RecSys API"},
    license_info={"name": "MIT"},
)

engine = create_engine("sqlite:///db0.db?check_same_thread=False")


# ── Database ──────────────────────────────────────────────────────────────────

@app.delete(
    "/clear_db",
    tags=["Database"],
    summary="Wipe all tables",
    description=(
        "Deletes **all rows** from every table in the database. "
        "The schema (table structure) is preserved. "
        "\n\n> ⚠️ This action is **irreversible**. Use only in test/dev environments."
    ),
    response_description="Confirmation message",
)
async def clear_db(request: Request):
    with engine.begin() as conn:
        inspector = inspect(engine)
        for table_name in inspector.get_table_names():
            conn.execute(text(f"DELETE FROM {table_name}"))
    return {"detail": "Database cleared successfully"}


# ── Items ─────────────────────────────────────────────────────────────────────

@app.post(
    "/item",
    tags=["Items"],
    summary="Add items to the catalogue",
    description=(
        "Insert one or more items into the `items` table in a single request.\n\n"
        "**Fields:**\n"
        "- `itemId` — must be unique across the catalogue.\n"
        "- `title` — used as the seed for collaborative filtering (`sel_item` parameter).\n"
        "- `description` + `tag` — combined and fed to TF-IDF for content-based similarity.\n\n"
        "Existing items with the same `itemId` are **not** updated — use `PUT /item/{item_id}` instead."
    ),
    response_description="Confirmation message",
)
async def add_items_to_items(items_data: ItemList):
    with engine.begin() as connection:
        for item in items_data.items:
            connection.execute(
                text("INSERT INTO items (itemId, title, description, tag) VALUES (:itemId, :title, :description, :tag)"),
                {"itemId": item.itemId, "title": item.title, "description": item.description, "tag": json.dumps(item.tag)},
            )
    return {"detail": "Items added to items successfully"}


@app.get(
    "/items",
    tags=["Items"],
    summary="List all items",
    description="Returns every item currently stored in the catalogue, including their `itemId`, `title`, `description`, and `tag` fields.",
    response_description="Array of item objects",
)
def get_items():
    with engine.begin() as conn:
        result = pd.read_sql_query(text("SELECT * FROM items"), conn)
    return json.loads(result.to_json(orient="records"))


@app.put(
    "/item/{item_id}",
    tags=["Items"],
    summary="Update an item",
    description=(
        "Replace the `title`, `description`, and `tag` of an existing item.\n\n"
        "- Returns **404** if no item with `item_id` exists.\n"
        "- The `itemId` itself cannot be changed; create a new item and delete the old one instead."
    ),
    response_description="Confirmation message",
)
async def update_item(item_id: str, request: Request):
    item_data = await request.json()
    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE items SET title = :title, description = :description, tag = :tag WHERE itemId = :itemId"),
            {"itemId": item_id, "title": item_data["title"], "description": item_data["description"], "tag": json.dumps(item_data["tag"])},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")
    return {"detail": "Item updated successfully"}


@app.delete(
    "/item",
    tags=["Items"],
    summary="Delete an item",
    description=(
        "Remove an item from the catalogue by `itemId`.\n\n"
        "**Request body:** `{\"itemId\": \"<id>\"}`\n\n"
        "Note: associated ratings or events referencing this `itemId` are **not** automatically removed."
    ),
    response_description="The deleted item payload echoed back",
)
async def delete_item(request: Request):
    item = await request.json()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM items WHERE itemId = :itemId"), item)
    return item


# ── Users ─────────────────────────────────────────────────────────────────────

@app.post(
    "/user",
    tags=["Users"],
    summary="Add user ratings",
    description=(
        "Insert one or more explicit user–item ratings.\n\n"
        "**Request body example:**\n"
        "```json\n"
        "{\n"
        '  "items": [\n'
        '    { "userId": "user_7", "itemId": "item_42", "rating": 4.5, "timestamp": 1716300000 }\n'
        "  ]\n"
        "}\n"
        "```\n\n"
        "- `rating` should be a numeric score (e.g. 0–5).\n"
        "- `timestamp` is a Unix epoch integer.\n"
        "- These records are the **primary input** for collaborative filtering."
    ),
    response_description="Confirmation message",
)
async def add_items_to_user(request: Request):
    item_user_data = await request.json()
    with engine.begin() as conn:
        for item in item_user_data["items"]:
            conn.execute(
                text("INSERT INTO users (userId, itemId, rating, timestamp) VALUES (:userId, :itemId, :rating, :timestamp)"),
                {"userId": item["userId"], "itemId": item["itemId"], "rating": item["rating"], "timestamp": item["timestamp"]},
            )
    return {"detail": "Ratings added successfully"}


@app.get(
    "/users",
    tags=["Users"],
    summary="List all ratings",
    description="Returns every user–item rating record in the database. Useful for data inspection or export.",
    response_description="Array of rating objects (`userId`, `itemId`, `rating`, `timestamp`)",
)
def get_users():
    with engine.begin() as conn:
        result = pd.read_sql_query(text("SELECT * FROM users"), conn)
    return json.loads(result.to_json(orient="records"))


@app.get(
    "/user",
    tags=["Users"],
    summary="Get ratings for a user",
    description=(
        "Fetch all rating records belonging to a specific user.\n\n"
        "**Request body:** `{\"userId\": \"<id>\"}`"
    ),
    response_description="Array of rating objects for the requested user",
)
async def get_user(request: Request):
    user = await request.json()
    with engine.begin() as conn:
        result = pd.read_sql_query(text("SELECT * FROM users WHERE userId = :userId"), conn, params=user)
    return json.loads(result.to_json(orient="records"))


@app.put(
    "/user/{user_id}",
    tags=["Users"],
    summary="Update user ratings",
    description=(
        "Update `rating` and `timestamp` for one or more existing user–item pairs.\n\n"
        "- Returns **404** if the `userId` / `itemId` combination does not exist.\n"
        "- Use `POST /user` to add new ratings."
    ),
    response_description="Confirmation message",
)
async def update_user(user_id: str, request: Request):
    user_data = await request.json()
    with engine.begin() as conn:
        for item in user_data["items"]:
            result = conn.execute(
                text("UPDATE users SET rating = :rating, timestamp = :timestamp WHERE userId = :userId AND itemId = :itemId"),
                {"userId": user_id, "itemId": item["itemId"], "rating": item["rating"], "timestamp": item["timestamp"]},
            )
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"User '{user_id}' or item '{item['itemId']}' not found",
                )
    return {"detail": "User ratings updated successfully"}


@app.delete(
    "/user",
    tags=["Users"],
    summary="Delete a user",
    description=(
        "Remove **all rating records** for a given user.\n\n"
        "**Request body:** `{\"userId\": \"<id>\"}`"
    ),
    response_description="The deleted user payload echoed back",
)
async def delete_user(request: Request):
    user = await request.json()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE userId = :userId"), user)
    return user


# ── Events ────────────────────────────────────────────────────────────────────

@app.post(
    "/event",
    tags=["Events"],
    summary="Record an implicit feedback event",
    description=(
        "Log a single implicit feedback event (click, view, purchase, etc.).\n\n"
        "**Request body:** `{\"userId\": \"...\", \"itemId\": \"...\", \"rating\": <float>, \"timestamp\": <unix>}`\n\n"
        "Events are stored in a separate `events` table from explicit ratings, "
        "allowing you to keep implicit and explicit signals distinct."
    ),
    response_description="The recorded event payload echoed back",
)
async def post_event(request: Request):
    event = await request.json()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO events (userId, itemId, rating, timestamp) VALUES (:userId, :itemId, :rating, :timestamp)"),
            event,
        )
    return event


@app.get(
    "/events",
    tags=["Events"],
    summary="List all events",
    description="Returns every event record in the database.",
    response_description="Array of event objects",
)
def get_all_events():
    with engine.begin() as conn:
        result = pd.read_sql_query(text("SELECT * FROM events"), conn)
    return json.loads(result.to_json(orient="records"))


@app.get(
    "/user/events",
    tags=["Events"],
    summary="Get events for a user",
    description=(
        "Fetch all event records for a specific user.\n\n"
        "**Request body:** `{\"userId\": \"<id>\"}`"
    ),
    response_description="Array of event objects for the requested user",
)
async def get_user_events(request: Request):
    user = await request.json()
    with engine.begin() as conn:
        result = pd.read_sql_query(text("SELECT * FROM events WHERE userId = :userId"), conn, params=user)
    return json.loads(result.to_json(orient="records"))


@app.get(
    "/item/events",
    tags=["Events"],
    summary="Get events for an item",
    description=(
        "Fetch all event records associated with a specific item.\n\n"
        "**Request body:** `{\"itemId\": \"<id>\"}`"
    ),
    response_description="Array of event objects for the requested item",
)
async def get_item_events(request: Request):
    item = await request.json()
    with engine.begin() as conn:
        result = pd.read_sql_query(text("SELECT * FROM events WHERE itemId = :itemId"), conn, params=item)
    return json.loads(result.to_json(orient="records"))


# ── Recommendations ───────────────────────────────────────────────────────────

@app.get(
    "/user/recommendations",
    tags=["Recommendations"],
    summary="Collaborative filtering recommendations",
    description=(
        "Returns the top `nrec` items most similar to `sel_item` using "
        "**K-Nearest Neighbors with cosine similarity** on the user–item rating matrix.\n\n"
        "**How it works:**\n"
        "1. Builds a sparse item–user matrix from all stored ratings.\n"
        "2. Filters out items with fewer than 1 rating and inactive users.\n"
        "3. Fits a KNN model (cosine distance, brute-force search).\n"
        "4. Fuzzy-matches `sel_item` against item titles (≥ 60% ratio threshold).\n"
        "5. Returns the `nrec` nearest neighbours sorted by ascending distance.\n\n"
        "**Requirements:** at least some rating data must exist in the database.\n\n"
        "Each result includes: item metadata (`itemId`, `title`, `description`, `tag`), "
        "`rank` (1 = most similar), and `distance` (cosine distance; lower = more similar)."
    ),
    response_description="Ranked list of recommended items with metadata, rank, and cosine distance",
)
def get_user_rec(
    nrec: Optional[int] = Query(5, description="Number of recommendations to return"),
    sel_item: Optional[str] = Query(None, description="Title of the seed item — fuzzy matched against the catalogue"),
):
    return collaborative_filtering_rec.start(nrec, sel_item)


@app.get(
    "/item/neighbors",
    tags=["Recommendations"],
    summary="Content-based similar items",
    description=(
        "Returns the `nitems` most similar items to item at index `itemno` using "
        "**TF-IDF + cosine similarity** computed over each item's `description` and `tag` fields.\n\n"
        "**How it works:**\n"
        "1. Concatenates `description` and `tag` for every item.\n"
        "2. Builds a TF-IDF matrix (word n-grams 1–3, English stop-words removed).\n"
        "3. Computes pairwise cosine similarity.\n"
        "4. Returns the top `nitems` neighbours of item `itemno`.\n\n"
        "**No rating history needed** — works from day one (cold-start friendly).\n\n"
        "Each result includes: name, description, tags, and similarity score."
    ),
    response_description="Target item info plus ranked similar items with TF-IDF cosine scores",
)
async def get_similar_items(
    itemno: int = Query(1, description="Row index (0-based) of the target item in the catalogue"),
    nitems: int = Query(3, description="Number of similar items to return"),
):
    lis = content_based_rec.start(0, itemno, nitems)
    return {"Item_number": str(itemno), "API_exec_time": "0", "items": lis}


@app.post(
    "/train",
    tags=["Recommendations"],
    summary="Retrain the recommender model",
    description=(
        "Triggers a full retraining cycle of the recommendation model. "
        "Call this endpoint after significant changes to the ratings dataset "
        "to ensure recommendations reflect the latest data."
    ),
    response_description="Training result or status",
)
def post_train():
    return train.train_rec()


# ── System ────────────────────────────────────────────────────────────────────

@app.get(
    "/system",
    tags=["System"],
    summary="Server resource usage",
    description=(
        "Returns real-time server diagnostics:\n\n"
        "| Field | Description |\n"
        "|---|---|\n"
        "| `uptime` | How long the server has been running |\n"
        "| `total_ram` | Total RAM in MB |\n"
        "| `available_ram` | Available (free) RAM in MB |\n"
        "| `cpu_model` | CPU model name |\n"
        "| `cpu_clock` | CPU clock speed in MHz |\n"
        "| `database_size` | Size of the SQLite `db0.db` file on disk |"
    ),
    response_description="System stats object",
)
def get_system():
    uptime = subprocess.check_output("uptime").decode().strip()
    total_ram = subprocess.check_output("free -m | awk 'NR==2{print $2}'", shell=True).decode().strip()
    available_ram = subprocess.check_output("free -m | awk 'NR==2{print $7}'", shell=True).decode().strip()
    cpu_model = subprocess.check_output("cat /proc/cpuinfo | grep 'model name' | uniq | awk -F: '{print $2}'", shell=True).decode().strip()
    cpu_clock = subprocess.check_output("cat /proc/cpuinfo | grep 'cpu MHz' | uniq | awk -F: '{print $2}'", shell=True).decode().strip()
    current_dir = os.path.dirname(os.path.realpath(__file__))
    db_path = os.path.join(current_dir, "db0.db")
    database_size = subprocess.check_output(f"du -sh '{db_path}'", shell=True).decode().strip()
    return {
        "uptime": uptime,
        "total_ram": total_ram,
        "available_ram": available_ram,
        "cpu_model": cpu_model,
        "cpu_clock": cpu_clock,
        "database_size": database_size,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
