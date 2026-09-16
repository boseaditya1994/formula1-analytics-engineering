import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def runner():
    spec = importlib.util.spec_from_file_location(
        "daily_pipeline", Path(__file__).resolve().parents[1] / "scripts/daily_pipeline.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("ingest_code", [1, 2])
def test_failed_or_pending_ingestion_prevents_mart_refresh(ingest_code):
    module = runner()
    with (
        patch("sys.argv", ["daily_pipeline.py"]),
        patch.object(module, "FileLock"),
        patch.object(
            module.subprocess, "run", return_value=MagicMock(returncode=ingest_code)
        ) as run,
        pytest.raises(SystemExit) as error,
    ):
        module.main()
    assert error.value.code == ingest_code
    assert run.call_count == 1


def test_successful_ingestion_builds_marts_and_propagates_test_failure():
    module = runner()
    with (
        patch("sys.argv", ["daily_pipeline.py"]),
        patch.object(module, "FileLock"),
        patch.object(
            module.subprocess, "run", side_effect=[MagicMock(returncode=0), MagicMock(returncode=1)]
        ) as run,
        pytest.raises(SystemExit) as error,
    ):
        module.main()
    assert error.value.code == 1
    assert run.call_count == 2
    assert "build" in run.call_args.args[0]
