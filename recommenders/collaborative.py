"""
Collaborative filtering via K-Nearest Neighbours on the user–item rating matrix.

Algorithm:
  1. Load ratings and items from the DB.
  2. Build a sparse item–user matrix (items as rows, users as columns).
  3. Fit a KNN model with cosine distance.
  4. Fuzzy-match the query title against known item titles (≥ 60 % ratio).
  5. Return the n nearest neighbours with their metadata and cosine distances.
"""

import logging
import time
from typing import Any, Dict, List

import pandas as pd
from fuzzywuzzy import fuzz
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_POPULARITY_THRESHOLD = 1   # minimum ratings an item must have
_ACTIVITY_THRESHOLD = 1     # minimum ratings a user must have given
_MAX_RATINGS = 2_000_000    # cap to avoid memory issues on huge datasets


def _fuzzy_match(title_to_idx: Dict[str, int], query: str) -> int:
    matches = [
        (title, idx, fuzz.ratio(title.lower(), query.lower()))
        for title, idx in title_to_idx.items()
    ]
    matches = sorted(
        [(t, i, r) for t, i, r in matches if r >= 60],
        key=lambda x: x[2],
        reverse=True,
    )
    if not matches:
        raise ValueError(f"No item found matching '{query}' (fuzzy threshold: 60 %)")
    logger.info("Fuzzy match for '%s': %s", query, [m[0] for m in matches[:3]])
    return matches[0][1]


def recommend(engine: Engine, sel_item: str, n_recommendations: int) -> Dict[str, Any]:
    t_start = time.perf_counter()

    with engine.begin() as conn:
        df_items = pd.read_sql_query(text("SELECT * FROM items"), conn)
        df_ratings = pd.read_sql_query(text("SELECT * FROM users"), conn)

    df_ratings = df_ratings.head(_MAX_RATINGS)

    # Filter by popularity and user activity
    popular_items = set(
        df_ratings.groupby("itemId").size()
        .loc[lambda s: s >= _POPULARITY_THRESHOLD].index
    )
    df_ratings = df_ratings[df_ratings.itemId.isin(popular_items)]

    active_users = set(
        df_ratings.groupby("userId").size()
        .loc[lambda s: s >= _ACTIVITY_THRESHOLD].index
    )
    df_ratings = df_ratings[df_ratings.userId.isin(active_users)]

    t_data = time.perf_counter() - t_start
    t_rec_start = time.perf_counter()

    # Build sparse item–user matrix
    item_user_mat = df_ratings.pivot(index="itemId", columns="userId", values="rating").fillna(0)
    df_items_indexed = df_items.set_index("itemId")
    valid_mask = df_items_indexed.index.isin(item_user_mat.index)
    title_to_idx = {
        title: i
        for i, title in enumerate(df_items_indexed.loc[valid_mask, "title"])
    }
    mat_sparse = csr_matrix(item_user_mat.values)

    model = NearestNeighbors(metric="cosine", algorithm="brute", n_neighbors=20, n_jobs=-1)
    model.fit(mat_sparse)

    query_idx = _fuzzy_match(title_to_idx, sel_item)
    distances, indices = model.kneighbors(mat_sparse[query_idx], n_neighbors=n_recommendations + 1)

    raw = sorted(
        zip(indices.squeeze().tolist(), distances.squeeze().tolist()),
        key=lambda x: x[1],
    )[1:]  # drop the item itself (distance = 0)

    idx_to_title = {v: k for k, v in title_to_idx.items()}
    recommendations: List[Dict[str, Any]] = []
    for rank, (idx, dist) in enumerate(raw, start=1):
        with engine.begin() as conn:
            row = pd.read_sql_query(
                text(f"SELECT * FROM items WHERE title='{idx_to_title[idx]}'"), conn
            )
        entry = row.to_dict(orient="records")[0]
        entry["rank"] = rank
        entry["distance"] = dist
        recommendations.append(entry)

    t_rec = time.perf_counter() - t_rec_start
    t_total = time.perf_counter() - t_start

    return {
        "execution_time": {
            "total": round(t_total, 4),
            "data_processing": round(t_data, 4),
            "recommendation": round(t_rec, 4),
        },
        "recommendations": recommendations,
    }
