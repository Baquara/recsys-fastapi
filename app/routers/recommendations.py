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
    "/hybrid",
    summary="Hybrid recommendations",
    description=(
        "Combines **collaborative filtering** and **content-based** scores into a single ranking.\n\n"
        "**How it works:**\n"
        "1. Pulls a candidate pool from both algorithms (over-fetched 3×).\n"
        "2. Normalises both scores to a similarity in `[0, 1]`.\n"
        "3. Combines with a weighted average: `hybrid = α × collaborative + (1 − α) × content_based`.\n"
        "4. Returns the top-N items sorted by the combined score.\n\n"
        "**When to use:** sparse rating data, or when you want a smoother, more robust ranking "
        "than either method on its own.\n\n"
        "Each result exposes its individual `collaborative_score` and `content_score` for transparency."
    ),
    response_description="Recommendations with `hybrid_score`, `collaborative_score`, and `content_score`",
)
def hybrid_recommendations(
    sel_item: str = Query(..., description="Title of the seed item — fuzzy matched against the catalogue"),
    nrec: int = Query(5, ge=1, le=50, description="Number of recommendations to return"),
    alpha: float = Query(0.5, ge=0.0, le=1.0, description="Weight for the collaborative signal (1 − α weights content-based)"),
):
    try:
        return recommendation_service.get_hybrid(engine, sel_item, nrec, alpha)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/auto",
    summary="Self-configuring recommendation",
    description=(
        "**Self-configuring** endpoint: the system inspects the data available for the requested "
        "item and infers the most appropriate algorithm — the caller does **not** specify the method.\n\n"
        "**Decision tree (based on number of ratings for the seed item):**\n\n"
        "| Ratings | Method chosen | Why |\n"
        "|---|---|---|\n"
        "| `0` | `content_based` | Cold-start — no behavioural signal yet |\n"
        "| `1` to `4` | `hybrid` | Sparse signal — combine collaborative + content-based |\n"
        "| `5` or more | `collaborative` | Sufficient rating history for KNN |\n\n"
        "The response always includes:\n"
        "- `method` — the algorithm actually used\n"
        "- `reason` — human-readable explanation of the decision\n"
        "- `ratings_count` — how many ratings the seed item had at decision time"
    ),
    response_description="Recommendations + `method`, `reason`, and `ratings_count` metadata",
)
def auto_recommendations(
    sel_item: str = Query(..., description="Title of the seed item — fuzzy matched against the catalogue"),
    nrec: int = Query(5, ge=1, le=50, description="Number of recommendations to return"),
):
    try:
        return recommendation_service.get_auto(engine, sel_item, nrec)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
