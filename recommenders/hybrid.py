"""
Hybrid recommender combining collaborative filtering and content-based filtering.

Strategy:
  1. Pull a candidate pool from BOTH algorithms (over-fetch by HYBRID_POOL_MULTIPLIER×).
  2. Normalise each score to a similarity in [0, 1]:
       - Collaborative: similarity = 1 − cosine_distance
       - Content-based: score is already a TF-IDF cosine similarity
  3. Combine with a weighted average:
       hybrid = α × collaborative + (1 − α) × content_based
  4. Return the top-n items sorted by the combined score.

Items present in only one source contribute 0 to the other source's term.
Tunable via environment variables — see app/config.py.
"""

import logging
from typing import Any, Dict, List

import pandas as pd
from fuzzywuzzy import fuzz
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.config import settings
from recommenders import collaborative, content_based

logger = logging.getLogger(__name__)

DEFAULT_ALPHA = settings.hybrid_alpha


def recommend(
    engine: Engine,
    sel_item: str,
    n_recommendations: int,
    alpha: float = DEFAULT_ALPHA,
) -> Dict[str, Any]:
    pool = n_recommendations * settings.hybrid_pool_multiplier

    # Collaborative leg (may be unavailable for cold items)
    collab_recs: List[Dict[str, Any]] = []
    try:
        collab_recs = collaborative.recommend(engine, sel_item, pool).get("recommendations", [])
    except (ValueError, KeyError) as exc:
        logger.info("Collaborative leg unavailable: %s", exc)

    # Content-based leg — resolve title → row index via fuzzy match
    with engine.begin() as conn:
        df_items = pd.read_sql_query(text("SELECT * FROM items"), conn)

    matches = sorted(
        [(i, row["title"], fuzz.ratio(row["title"].lower(), sel_item.lower()))
         for i, row in df_items.iterrows()],
        key=lambda x: x[2], reverse=True,
    )
    best = next(
        ((i, t, r) for i, t, r in matches if r >= settings.fuzzy_match_threshold),
        None,
    )

    content_items: List[Dict[str, Any]] = []
    if best is not None:
        item_index, _, _ = best
        content_raw = content_based.recommend(engine, item_index, pool)
        content_items = [x for x in content_raw if "name" in x and "score" in x]

    if not collab_recs and not content_items:
        raise ValueError(f"No recommendations available for '{sel_item}'")

    # Unified score table keyed by item title
    scores: Dict[str, Dict[str, float]] = {}

    for rec in collab_recs:
        title = rec.get("title")
        if not title:
            continue
        sim = max(0.0, 1.0 - float(rec.get("distance", 1.0)))
        scores.setdefault(title, {"collab": 0.0, "content": 0.0})
        scores[title]["collab"] = sim

    for item in content_items:
        title = item.get("name")
        if not title:
            continue
        sim = float(item.get("score", 0))
        scores.setdefault(title, {"collab": 0.0, "content": 0.0})
        scores[title]["content"] = sim

    results = [
        {
            "title": title,
            "hybrid_score": round(alpha * data["collab"] + (1 - alpha) * data["content"], 6),
            "collaborative_score": round(data["collab"], 6),
            "content_score": round(data["content"], 6),
        }
        for title, data in scores.items()
    ]
    results.sort(key=lambda r: r["hybrid_score"], reverse=True)

    return {
        "alpha": alpha,
        "recommendations": results[:n_recommendations],
    }
