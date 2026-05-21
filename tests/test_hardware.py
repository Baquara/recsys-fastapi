import sys
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

import app.hardware as hw


@pytest.fixture(autouse=True)
def reset_backend():
    """Guarantee _effective_backend is 'none' after every test."""
    yield
    hw._effective_backend = "none"


# ── configure() ───────────────────────────────────────────────────────────────

def test_configure_none():
    assert hw.configure("none") == "none"
    assert hw.effective_backend() == "none"


def test_configure_unknown_falls_back_to_none():
    assert hw.configure("quantum") == "none"


def test_configure_intel_when_available():
    mock_sklearnex = MagicMock()
    with patch.dict(sys.modules, {"sklearnex": mock_sklearnex}):
        result = hw.configure("intel")
    assert result == "intel"
    mock_sklearnex.patch_sklearn.assert_called_once()


def test_configure_intel_when_unavailable():
    with patch.dict(sys.modules, {"sklearnex": None}):
        assert hw.configure("intel") == "none"


def test_configure_cuda_when_available():
    mock_cuml = MagicMock()
    with patch.dict(sys.modules, {"cuml": mock_cuml}):
        assert hw.configure("cuda") == "cuda"


def test_configure_cuda_when_unavailable():
    with patch.dict(sys.modules, {"cuml": None}):
        assert hw.configure("cuda") == "none"


# ── get_nearest_neighbors() ───────────────────────────────────────────────────

def test_get_nearest_neighbors_none_backend():
    from sklearn.neighbors import NearestNeighbors as SkNN
    nn = hw.get_nearest_neighbors(n_neighbors=2, metric="cosine", algorithm="brute")
    assert isinstance(nn, SkNN)


def test_get_nearest_neighbors_cuda_dispatches_to_cuml(monkeypatch):
    monkeypatch.setattr(hw, "_effective_backend", "cuda")
    mock_nn_instance = MagicMock()
    mock_neighbors = MagicMock()
    mock_neighbors.NearestNeighbors.return_value = mock_nn_instance
    mock_cuml = MagicMock()
    mock_cuml.neighbors = mock_neighbors
    with patch.dict(sys.modules, {"cuml": mock_cuml, "cuml.neighbors": mock_neighbors}):
        result = hw.get_nearest_neighbors(n_neighbors=3)
    assert result is mock_nn_instance


def test_get_nearest_neighbors_cuda_falls_back_when_cuml_missing(monkeypatch):
    monkeypatch.setattr(hw, "_effective_backend", "cuda")
    from sklearn.neighbors import NearestNeighbors as SkNN
    with patch.dict(sys.modules, {"cuml": None, "cuml.neighbors": None}):
        result = hw.get_nearest_neighbors(n_neighbors=2, metric="cosine", algorithm="brute")
    assert isinstance(result, SkNN)


# ── get_tfidf_vectorizer() ────────────────────────────────────────────────────

def test_get_tfidf_vectorizer_always_sklearn():
    from sklearn.feature_extraction.text import TfidfVectorizer
    assert isinstance(hw.get_tfidf_vectorizer(), TfidfVectorizer)


# ── compute_cosine_similarity() ───────────────────────────────────────────────

def test_compute_cosine_similarity_none_backend():
    X = np.array([[1.0, 0.0], [0.0, 1.0]])
    result = hw.compute_cosine_similarity(X)
    assert result.shape == (2, 2)
    np.testing.assert_allclose(result[0, 0], 1.0)
    np.testing.assert_allclose(result[0, 1], 0.0, atol=1e-6)


def test_compute_cosine_similarity_cuda_dispatches_to_cupy(monkeypatch):
    monkeypatch.setattr(hw, "_effective_backend", "cuda")
    expected = np.eye(2)
    mock_cp = MagicMock()
    mock_cp.asnumpy.return_value = expected
    X = np.array([[1.0, 0.0], [0.0, 1.0]])
    with patch.dict(sys.modules, {"cupy": mock_cp}):
        result = hw.compute_cosine_similarity(X)
    assert result is expected
    mock_cp.asarray.assert_called_once()


def test_compute_cosine_similarity_cuda_falls_back_when_cupy_missing(monkeypatch):
    monkeypatch.setattr(hw, "_effective_backend", "cuda")
    X = np.array([[1.0, 0.0], [0.0, 1.0]])
    with patch.dict(sys.modules, {"cupy": None}):
        result = hw.compute_cosine_similarity(X)
    assert result.shape == (2, 2)
