from dataclasses import dataclass, field


@dataclass
class Settings:
    database_url: str = "sqlite:///./db0.db"
    app_title: str = "Recommender System API"
    app_version: str = "1.0.0"
    app_description: str = """
A **general-purpose recommender system** built with FastAPI and SQLite.

## Algorithms

| Endpoint | Algorithm | When to use |
|---|---|---|
| `GET /recommendations/collaborative` | Collaborative Filtering — KNN cosine similarity on the user–item matrix | Enough rating history exists |
| `GET /recommendations/content-based` | Content-Based — TF-IDF cosine similarity on `description` + `tag` fields | Cold-start or sparse ratings |

## Typical workflow

1. **Load catalogue** — `POST /items` with your items.
2. **Load ratings** — `POST /users` with historical user–item scores.
3. **Get recommendations** — `GET /recommendations/collaborative?sel_item=Inception&nrec=10`.

> **Tip:** `sel_item` uses fuzzy matching, so partial or approximate titles are accepted.
"""
    tags_metadata: list = field(default_factory=lambda: [
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
                "Each record links a `userId` to an `itemId` with a numeric score (0–5) and a Unix timestamp. "
                "These ratings are the primary input for the collaborative filtering engine."
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
                "| `GET /recommendations/collaborative` | KNN collaborative filtering (cosine) | Rich rating history |\n"
                "| `GET /recommendations/content-based` | TF-IDF content-based (cosine) | Cold-start / new items |"
            ),
        },
        {
            "name": "Admin",
            "description": "Database maintenance and server health diagnostics.",
        },
    ])


settings = Settings()
