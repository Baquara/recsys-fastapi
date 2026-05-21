from typing import Any, Dict, List

import pandas as pd
from fuzzywuzzy import fuzz
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.config import settings
from recommenders import collaborative, content_based, hybrid


def get_collaborative(engine: Engine, sel_item: str, n_recommendations: int) -> Dict[str, Any]:
    return collaborative.recommend(engine, sel_item, n_recommendations)


def get_content_based(engine: Engine, item_index: int, n_items: int) -> List[Dict[str, Any]]:
    return content_based.recommend(engine, item_index, n_items)


def get_hybrid(
    engine: Engine,
    sel_item: str,
    n_recommendations: int,
    alpha: float = hybrid.DEFAULT_ALPHA,
) -> Dict[str, Any]:
    return hybrid.recommend(engine, sel_item, n_recommendations, alpha)


def get_auto(engine: Engine, sel_item: str, n_recommendations: int) -> Dict[str, Any]:
    """
    Self-configuring recommender: inspects available data for the requested
    item and picks the most appropriate algorithm without the caller specifying it.

    Decision tree (thresholds configurable via env vars):
      - 0 ratings                              → content_based  (cold-start)
      - 1 .. HYBRID_THRESHOLD-1 ratings        → hybrid         (combine signals)
      - >= HYBRID_THRESHOLD ratings            → collaborative  (sufficient signal)
    """
    with engine.begin() as conn:
        df_items = pd.read_sql_query(text("SELECT * FROM items"), conn)
        df_ratings = pd.read_sql_query(text("SELECT * FROM users"), conn)

    matches = sorted(
        [(i, row["title"], fuzz.ratio(row["title"].lower(), sel_item.lower()))
         for i, row in df_items.iterrows()],
        key=lambda x: x[2], reverse=True,
    )
    best = next(
        ((i, t, r) for i, t, r in matches if r >= settings.fuzzy_match_threshold),
        None,
    )
    if best is None:
        raise ValueError(f"No item found matching '{sel_item}'")

    item_index, matched_title, _ = best
    item_id = int(df_items.iloc[item_index]["itemId"])
    ratings_count = int((df_ratings["itemId"] == item_id).sum())

    if ratings_count == 0:
        return {
            "method": "content_based",
            "reason": f"item '{matched_title}' has no ratings (cold-start)",
            "ratings_count": 0,
            "items": content_based.recommend(engine, item_index, n_recommendations),
        }
    elif ratings_count < settings.hybrid_threshold:
        return {
            "method": "hybrid",
            "reason": (
                f"item '{matched_title}' has {ratings_count} rating(s) — "
                f"below threshold ({settings.hybrid_threshold}), combining signals"
            ),
            "ratings_count": ratings_count,
            **hybrid.recommend(engine, sel_item, n_recommendations),
        }
    else:
        return {
            "method": "collaborative",
            "reason": (
                f"item '{matched_title}' has {ratings_count} ratings — "
                f"at or above threshold ({settings.hybrid_threshold}), sufficient signal"
            ),
            "ratings_count": ratings_count,
            **collaborative.recommend(engine, sel_item, n_recommendations),
        }
