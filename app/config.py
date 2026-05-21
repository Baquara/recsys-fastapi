import os
from dataclasses import dataclass, field


def _int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))


def _float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))


def _str(key: str, default: str) -> str:
    return os.getenv(key, default)


def _bool(key: str, default: bool) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes")


@dataclass
class Settings:
    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = field(
        default_factory=lambda: _str("DATABASE_URL", "sqlite:///./data/db0.db")
    )

    # ── Server ───────────────────────────────────────────────────────────────
    app_host: str = field(default_factory=lambda: _str("APP_HOST", "0.0.0.0"))
    app_port: int = field(default_factory=lambda: _int("APP_PORT", 8000))
    app_reload: bool = field(default_factory=lambda: _bool("APP_RELOAD", False))

    # ── Auto-selection ────────────────────────────────────────────────────────
    # Items with fewer ratings than this use hybrid; at or above it → collaborative.
    hybrid_threshold: int = field(
        default_factory=lambda: _int("HYBRID_THRESHOLD", 5)
    )

    # ── Hybrid recommender ───────────────────────────────────────────────────
    hybrid_alpha: float = field(
        default_factory=lambda: _float("HYBRID_ALPHA", 0.5)
    )
    # Candidate pool = nrec × this multiplier (larger → better recall, slower)
    hybrid_pool_multiplier: int = field(
        default_factory=lambda: _int("HYBRID_POOL_MULTIPLIER", 3)
    )

    # ── Collaborative filtering ──────────────────────────────────────────────
    # Items with fewer ratings than this are excluded from the matrix
    collab_popularity_threshold: int = field(
        default_factory=lambda: _int("COLLAB_POPULARITY_THRESHOLD", 1)
    )
    # Users with fewer ratings than this are excluded from the matrix
    collab_activity_threshold: int = field(
        default_factory=lambda: _int("COLLAB_ACTIVITY_THRESHOLD", 1)
    )
    # Hard cap on rows loaded from the ratings table (memory guard)
    collab_max_ratings: int = field(
        default_factory=lambda: _int("COLLAB_MAX_RATINGS", 2_000_000)
    )
    # k for the KNN model (must be > max nrec the API can return)
    collab_n_neighbors: int = field(
        default_factory=lambda: _int("COLLAB_N_NEIGHBORS", 20)
    )

    # ── Content-based filtering ──────────────────────────────────────────────
    # Upper bound of TF-IDF n-gram range (lower bound is always 1)
    content_ngram_max: int = field(
        default_factory=lambda: _int("CONTENT_NGRAM_MAX", 3)
    )
    # Minimum document frequency for a term to be included in the TF-IDF matrix
    content_min_df: int = field(
        default_factory=lambda: _int("CONTENT_MIN_DF", 1)
    )

    # ── Fuzzy matching (shared by all recommenders) ──────────────────────────
    # Minimum fuzz.ratio score (0–100) to accept a title match
    fuzzy_match_threshold: int = field(
        default_factory=lambda: _int("FUZZY_MATCH_THRESHOLD", 60)
    )

    # ── App metadata (not env-configurable) ──────────────────────────────────
    app_title: str = "Recommender System API"
    app_version: str = "1.0.0"
    app_description: str = """
A **general-purpose recommender system** built with FastAPI and SQLite.

## Algorithms

| Endpoint | Algorithm | When to use |
|---|---|---|
| `GET /recommendations/collaborative` | Collaborative Filtering — KNN cosine similarity on the user–item matrix | Enough rating history exists |
| `GET /recommendations/content-based` | Content-Based — TF-IDF cosine similarity on `description` + `tag` fields | Cold-start or sparse ratings |
| `GET /recommendations/hybrid` | Hybrid — weighted combination of both | Sparse data or smoother ranking |
| `GET /recommendations/auto` | Self-configuring — infers the best method from available data | General use |

## Typical workflow

1. **Load catalogue** — `POST /items` with your items.
2. **Load ratings** — `POST /users` with historical user–item scores.
3. **Get recommendations** — `GET /recommendations/auto?sel_item=Inception&nrec=10`.
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
                "| `GET /recommendations/content-based` | TF-IDF content-based (cosine) | Cold-start / new items |\n"
                "| `GET /recommendations/hybrid` | Weighted combination of both | Sparse data |\n"
                "| `GET /recommendations/auto` | Self-configuring | General use |"
            ),
        },
        {
            "name": "Admin",
            "description": "Database maintenance and server health diagnostics.",
        },
    ])


settings = Settings()
