import pytest
from unittest.mock import patch
from app.config import settings
from recommenders import collaborative, content_based, hybrid


# ── Helpers ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def small_knn(monkeypatch):
    """Reduce n_neighbors so KNN works with the small test dataset."""
    monkeypatch.setattr(settings, "collab_n_neighbors", 7)
    monkeypatch.setattr(settings, "hybrid_pool_multiplier", 2)


# ── Collaborative ─────────────────────────────────────────────────────────────

def test_collaborative_fuzzy_match_no_result(rec_engine):
    with pytest.raises(ValueError, match="No item found"):
        collaborative.recommend(rec_engine, "xxxxxxxxxxxxxxxxxxx", 3)


def test_collaborative_returns_recommendations(rec_engine):
    result = collaborative.recommend(rec_engine, "Alpha", 3)
    assert "recommendations" in result
    assert len(result["recommendations"]) == 3
    assert "execution_time" in result


def test_collaborative_execution_times_present(rec_engine):
    result = collaborative.recommend(rec_engine, "Beta", 2)
    times = result["execution_time"]
    assert "total" in times and "data_processing" in times and "recommendation" in times


# ── Content-based ─────────────────────────────────────────────────────────────

def test_content_based_returns_similar_items(rec_engine):
    result = content_based.recommend(rec_engine, 0, 2)
    # First entry is the target, last is timing, middle are recommendations
    assert result[0]["target"]["name"] == "Alpha"
    recs = [x for x in result if "position" in x]
    assert len(recs) == 2


def test_content_based_timing_entry(rec_engine):
    result = content_based.recommend(rec_engine, 0, 1)
    timing = result[-1]
    assert "endpoint_execution_time" in timing


# ── Hybrid ────────────────────────────────────────────────────────────────────

def test_hybrid_combines_both_legs(rec_engine):
    result = hybrid.recommend(rec_engine, "Alpha", 3)
    assert "recommendations" in result
    assert result["alpha"] == settings.hybrid_alpha
    recs = result["recommendations"]
    assert len(recs) <= 3
    for r in recs:
        assert "hybrid_score" in r
        assert "collaborative_score" in r
        assert "content_score" in r


def test_hybrid_custom_alpha(rec_engine):
    result = hybrid.recommend(rec_engine, "Alpha", 2, alpha=0.8)
    assert result["alpha"] == 0.8


def test_hybrid_collab_unavailable_falls_back_to_content(rec_engine):
    """When collaborative raises, hybrid should still work using content-based only."""
    with patch("recommenders.hybrid.collaborative.recommend", side_effect=ValueError("no match")):
        result = hybrid.recommend(rec_engine, "Alpha", 2)
    assert "recommendations" in result
    # All scores come from content-based only
    for r in result["recommendations"]:
        assert r["collaborative_score"] == 0.0


def test_hybrid_no_candidates_raises(rec_engine):
    """When both legs yield nothing, hybrid raises ValueError."""
    with patch("recommenders.hybrid.collaborative.recommend", side_effect=ValueError("x")):
        with patch("recommenders.hybrid.content_based.recommend", return_value=[{"target": {}}]):
            with pytest.raises(ValueError, match="No recommendations available"):
                hybrid.recommend(rec_engine, "Alpha", 2)


def test_hybrid_skips_collab_rec_without_title(rec_engine):
    """Collab recs with title=None are skipped; content-based still produces results."""
    with patch("recommenders.hybrid.collaborative.recommend",
               return_value={"recommendations": [{"distance": 0.2, "title": None}]}):
        result = hybrid.recommend(rec_engine, "Alpha", 2)
    assert "recommendations" in result
    for r in result["recommendations"]:
        assert r["collaborative_score"] == 0.0


def test_hybrid_skips_content_item_with_empty_name(rec_engine):
    """Content items where name is empty string are skipped; collab still produces results."""
    with patch("recommenders.hybrid.content_based.recommend",
               return_value=[{"name": "", "score": 0.5}]):
        result = hybrid.recommend(rec_engine, "Alpha", 2)
    assert "recommendations" in result
    for r in result["recommendations"]:
        assert r["content_score"] == 0.0
