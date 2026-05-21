from fastapi import APIRouter, HTTPException, Query
from app.database import engine
from app.services import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get(
    "/collaborative",
    summary="Collaborative filtering recommendations",
    description=(
        "Returns the top `nrec` items most similar to `sel_item` using "
        "**K-Nearest Neighbours with cosine similarity** on the user–item rating matrix.\n\n"
        "**How it works:**\n"
        "1. Builds a sparse item–user matrix from all stored ratings.\n"
        "2. Filters out items with fewer than 1 rating and inactive users.\n"
        "3. Fits a KNN model (cosine distance, brute-force).\n"
        "4. Fuzzy-matches `sel_item` against item titles (≥ 60 % threshold).\n"
        "5. Returns the `nrec` nearest neighbours sorted by ascending distance.\n\n"
        "**Requirements:** rating data must exist in the database.\n\n"
        "Each result contains: item metadata, `rank` (1 = most similar), "
        "and `distance` (cosine distance — lower means more similar)."
    ),
    response_description="Execution time breakdown + ranked list of recommended items",
)
def collaborative_recommendations(
    sel_item: str = Query(..., description="Title of the seed item — fuzzy matched against the catalogue", examples=["Eiffel Tower"]),
    nrec: int = Query(5, ge=1, le=50, description="Number of recommendations to return"),
):
    try:
        return recommendation_service.get_collaborative(engine, sel_item, nrec)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/content-based",
    summary="Content-based similar items",
    description=(
        "Returns the `n` most similar items to the item at row index `item_index` using "
        "**TF-IDF + cosine similarity** computed over `description` and `tag` fields.\n\n"
        "**How it works:**\n"
        "1. Concatenates `description` and `tag` for every item in the catalogue.\n"
        "2. Builds a TF-IDF matrix (word n-grams 1–3, English stop-words removed).\n"
        "3. Computes pairwise cosine similarity.\n"
        "4. Returns the top `n` neighbours of item at row `item_index`.\n\n"
        "**No rating history needed** — works from day one (cold-start friendly)."
    ),
    response_description="Target item info + ranked similar items with TF-IDF cosine scores",
)
def content_based_recommendations(
    item_index: int = Query(0, ge=0, description="Row index (0-based) of the target item in the catalogue"),
    n: int = Query(3, ge=1, le=50, description="Number of similar items to return"),
):
    try:
        return recommendation_service.get_content_based(engine, item_index, n)
    except (IndexError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=f"Item index out of range: {exc}")


@router.get(
    "/auto",
    summary="Auto-select recommendation algorithm",
    description=(
        "Infers the best recommendation algorithm based on available data for the requested item.\n\n"
        "**Decision logic:**\n"
        "- Item has ratings in the database → **Collaborative Filtering** (KNN cosine)\n"
        "- Item has no ratings (cold-start) → **Content-Based** (TF-IDF cosine)\n\n"
        "The response always includes a `method` field indicating which algorithm was used."
    ),
    response_description="Recommendations + `method` field indicating the algorithm chosen",
)
def auto_recommendations(
    sel_item: str = Query(..., description="Title of the seed item — fuzzy matched against the catalogue"),
    nrec: int = Query(5, ge=1, le=50, description="Number of recommendations to return"),
):
    try:
        return recommendation_service.get_auto(engine, sel_item, nrec)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
