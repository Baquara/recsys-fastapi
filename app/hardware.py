"""
Hardware acceleration layer for recommendation algorithms.

Configured via the HARDWARE_BACKEND environment variable:

  none  (default) — standard CPU sklearn, no extra dependencies required
  intel           — Intel Extension for Scikit-learn (scikit-learn-intelex):
                    patches sklearn globally to use MKL/DNNL on Intel CPUs.
                    Drop-in: all sklearn calls in recommenders are accelerated
                    transparently with no further code changes.
  cuda            — RAPIDS cuML + CuPy: GPU-accelerated NearestNeighbors (cuML)
                    and cosine-similarity matrix computation (CuPy).
                    TF-IDF vectorisation stays on CPU (no cuML text counterpart).

If the requested library is not installed the module logs a warning and
falls back to the 'none' backend automatically.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_effective_backend: str = "none"


# ── Public API ─────────────────────────────────────────────────────────────────

def configure(backend: str) -> str:
    """Initialise the requested backend. Returns the effective backend name."""
    global _effective_backend
    b = backend.lower().strip()
    if b == "intel":
        _effective_backend = _try_intel()
    elif b == "cuda":
        _effective_backend = _try_cuda()
    else:
        _effective_backend = "none"
    logger.info("Hardware backend: %s", _effective_backend)
    return _effective_backend


def effective_backend() -> str:
    """Return the currently active backend name."""
    return _effective_backend


def get_nearest_neighbors(**kwargs) -> Any:
    """Return a NearestNeighbors instance for the active backend."""
    if _effective_backend == "cuda":
        try:
            from cuml.neighbors import NearestNeighbors
            return NearestNeighbors(**kwargs)
        except ImportError:
            pass
    from sklearn.neighbors import NearestNeighbors
    return NearestNeighbors(**kwargs)


def get_tfidf_vectorizer(**kwargs) -> Any:
    """Return a TfidfVectorizer instance. cuML has no text vectorizer; always sklearn."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    return TfidfVectorizer(**kwargs)


def compute_cosine_similarity(matrix) -> Any:
    """Compute full pairwise cosine similarity. Offloads to CuPy on the cuda backend."""
    if _effective_backend == "cuda":
        try:
            import cupy as cp
            arr = matrix.toarray() if hasattr(matrix, "toarray") else matrix
            gpu = cp.asarray(arr, dtype=cp.float32)
            norms = cp.linalg.norm(gpu, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            normed = gpu / norms
            return cp.asnumpy(normed @ normed.T)
        except ImportError:
            pass
    from sklearn.metrics.pairwise import linear_kernel
    return linear_kernel(matrix, matrix)


# ── Private helpers ────────────────────────────────────────────────────────────

def _try_intel() -> str:
    try:
        from sklearnex import patch_sklearn
        patch_sklearn()
        logger.info("Intel Extension for Scikit-learn enabled")
        return "intel"
    except ImportError:
        logger.warning(
            "HARDWARE_BACKEND=intel requested but 'scikit-learn-intelex' is not "
            "installed; falling back to standard sklearn."
        )
        return "none"


def _try_cuda() -> str:
    try:
        import cuml  # noqa: F401
        logger.info("RAPIDS cuML GPU acceleration enabled")
        return "cuda"
    except ImportError:
        logger.warning(
            "HARDWARE_BACKEND=cuda requested but 'cuml' is not installed; "
            "falling back to standard sklearn."
        )
        return "none"
