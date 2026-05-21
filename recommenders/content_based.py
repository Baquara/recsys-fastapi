"""
Content-based filtering via TF-IDF cosine similarity.

Algorithm:
  1. Load items from the DB.
  2. Build a TF-IDF matrix over concatenated `description` + `tag` text.
  3. Compute pairwise cosine similarities.
  4. Return the top-n most similar items to the query item (by row index).

Tunable via environment variables — see app/config.py.
"""

import logging
import time
from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from app import hardware
from app.config import settings

logger = logging.getLogger(__name__)


def _build_similarity_index(df: pd.DataFrame) -> Dict[Any, List]:
    tf = hardware.get_tfidf_vectorizer(
        analyzer="word",
        ngram_range=(1, settings.content_ngram_max),
        min_df=settings.content_min_df,
        stop_words="english",
    )
    tfidf_matrix = tf.fit_transform(df["description"] + " | " + df["tag"])
    cosine_sim = hardware.compute_cosine_similarity(tfidf_matrix)

    results: Dict[Any, List] = {}
    for idx, row in df.iterrows():
        similar_indices = cosine_sim[idx].argsort()[:-100:-1]
        results[int(row["itemId"])] = [
            (float(cosine_sim[idx][i]), int(df["itemId"][i])) for i in similar_indices
        ][1:]  # exclude self

    return results


def recommend(engine: Engine, item_index: int, n_items: int) -> List[Dict[str, Any]]:
    t_start = time.perf_counter()

    with engine.begin() as conn:
        df = pd.read_sql_query(text("SELECT * FROM items"), conn)

    t_data = time.perf_counter() - t_start
    t_rec_start = time.perf_counter()

    similarity_index = _build_similarity_index(df)

    target_id = int(df.iloc[item_index]["itemId"])
    target_title = str(df.iloc[item_index]["title"])

    neighbours = similarity_index[target_id][:n_items]

    results: List[Dict[str, Any]] = [
        {
            "target": {
                "name": target_title,
                "id": target_id,
                "requested_n": n_items,
            }
        }
    ]
    for position, (score, neighbour_id) in enumerate(neighbours, start=1):
        row = df.loc[df["itemId"] == neighbour_id].iloc[0]
        results.append({
            "position": position,
            "name": str(row["title"]),
            "description": str(row["description"]),
            "tags": str(row["tag"]),
            "score": str(float(score)),
        })

    t_rec = time.perf_counter() - t_rec_start
    t_total = time.perf_counter() - t_start

    results.append({
        "endpoint_execution_time": str(round(t_total, 4)),
        "data_processing_time": str(round(t_data, 4)),
        "rec_exec_time": str(round(t_rec, 4)),
    })

    return results
