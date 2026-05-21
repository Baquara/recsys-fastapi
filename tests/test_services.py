import pytest
from unittest.mock import patch, MagicMock
from app.config import settings
from app.services import recommendation_service, system_service


# ── recommendation_service ────────────────────────────────────────────────────

@patch("app.services.recommendation_service.collaborative.recommend")
def test_get_collaborative(mock_rec, rec_engine):
    mock_rec.return_value = {"recommendations": [], "execution_time": {}}
    result = recommendation_service.get_collaborative(rec_engine, "Alpha", 3)
    mock_rec.assert_called_once_with(rec_engine, "Alpha", 3)
    assert "recommendations" in result


@patch("app.services.recommendation_service.content_based.recommend")
def test_get_content_based(mock_rec, rec_engine):
    mock_rec.return_value = [{"target": {}}]
    result = recommendation_service.get_content_based(rec_engine, 0, 3)
    mock_rec.assert_called_once_with(rec_engine, 0, 3)


@patch("app.services.recommendation_service.hybrid.recommend")
def test_get_hybrid(mock_rec, rec_engine):
    mock_rec.return_value = {"alpha": 0.5, "recommendations": []}
    result = recommendation_service.get_hybrid(rec_engine, "Alpha", 3, alpha=0.5)
    mock_rec.assert_called_once_with(rec_engine, "Alpha", 3, 0.5)


# ── get_auto paths ────────────────────────────────────────────────────────────

def test_get_auto_no_match_raises(rec_engine):
    with pytest.raises(ValueError, match="No item found"):
        recommendation_service.get_auto(rec_engine, "zzzzzzzzzzz", 3)


@patch("app.services.recommendation_service.content_based.recommend")
def test_get_auto_cold_start(mock_cb, rec_engine):
    """Item 7 (Eta) has 0 ratings → content_based."""
    mock_cb.return_value = [{"target": {}}]
    result = recommendation_service.get_auto(rec_engine, "Eta", 3)
    assert result["method"] == "content_based"
    assert result["ratings_count"] == 0
    mock_cb.assert_called_once()


@patch("app.services.recommendation_service.hybrid.recommend")
def test_get_auto_hybrid_path(mock_h, rec_engine, monkeypatch):
    """Item 8 (Theta) has 3 ratings, threshold=5 → hybrid."""
    monkeypatch.setattr(settings, "hybrid_threshold", 5)
    mock_h.return_value = {"alpha": 0.5, "recommendations": []}
    result = recommendation_service.get_auto(rec_engine, "Theta", 3)
    assert result["method"] == "hybrid"
    assert result["ratings_count"] == 3
    mock_h.assert_called_once()


@patch("app.services.recommendation_service.collaborative.recommend")
def test_get_auto_collaborative_path(mock_c, rec_engine, monkeypatch):
    """Items 1-6 have 6 ratings each, threshold=5 → collaborative."""
    monkeypatch.setattr(settings, "hybrid_threshold", 5)
    mock_c.return_value = {"recommendations": [], "execution_time": {}}
    result = recommendation_service.get_auto(rec_engine, "Alpha", 3)
    assert result["method"] == "collaborative"
    assert result["ratings_count"] == 6
    mock_c.assert_called_once()


# ── system_service ────────────────────────────────────────────────────────────

def test_get_system_info():
    with patch("app.services.system_service.subprocess.check_output", return_value=b"mocked\n"):
        info = system_service.get_system_info("/fake/db.db")
    assert info.uptime == "mocked"
    assert info.total_ram_mb == "mocked"
    assert info.database_size == "mocked"


def test_get_system_info_fields_populated():
    with patch("app.services.system_service.subprocess.check_output", return_value=b"value\n"):
        info = system_service.get_system_info("/fake/db.db")
    assert info.available_ram_mb == "value"
    assert info.cpu_model == "value"
    assert info.cpu_clock_mhz == "value"
