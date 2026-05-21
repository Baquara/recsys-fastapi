import runpy
from unittest.mock import patch


def test_run_calls_uvicorn():
    with patch("uvicorn.run") as mock_run:
        runpy.run_path("run.py", run_name="__main__")
    mock_run.assert_called_once()
    _, kwargs = mock_run.call_args
    assert kwargs["host"] is not None
    assert kwargs["port"] is not None
