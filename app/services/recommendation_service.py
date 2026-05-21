from typing import Any, Dict, List
import pandas as pd
from fuzzywuzzy import fuzz
from sqlalchemy import text
from sqlalchemy.engine import Engine
from recommenders import collaborative, content_based


def get_collaborative(engine: Engine, sel_item: str, n_recommendations: int) -> Dict[str, Any]:
    return collaborative.recommend(engine, sel_item, n_recommendations)


def get_content_based(engine: Engine, item_index: int, n_items: int) -> List[Dict[str, Any]]:
    return content_based.recommend(engine, item_index, n_items)


def get_auto(engine: Engine, sel_item: str, n_recommendations: int) -> Dict[str, Any]:
    with engine.begin() as conn:
        df_items = pd.read_sql_query(text("SELECT * FROM items"), conn)
        df_ratings = pd.read_sql_query(text("SELECT * FROM users"), conn)

    # Fuzzy-match the title to find the item
    matches = sorted(
        [(i, row["title"], fuzz.ratio(row["title"].lower(), sel_item.lower()))
         for i, row in df_items.iterrows()],
        key=lambda x: x[2], reverse=True,
    )
    best = next(((i, t, r) for i, t, r in matches if r >= 60), None)
    if best is None:
        raise ValueError(f"No item found matching '{sel_item}'")

    item_index, matched_title, _ = best
    item_id = int(df_items.iloc[item_index]["itemId"])

    has_ratings = not df_ratings[df_ratings["itemId"] == item_id].empty

    if has_ratings:
        result = collaborative.recommend(engine, sel_item, n_recommendations)
        return {"method": "collaborative", **result}
    else:
        result = content_based.recommend(engine, item_index, n_recommendations)
        return {"method": "content_based", "items": result}
