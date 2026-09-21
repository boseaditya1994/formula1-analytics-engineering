import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def runner():
    spec = importlib.util.spec_from_file_location(
        "race_week_pipeline",
        Path(__file__).resolve().parents[1] / "scripts/race_week_pipeline.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("ingest_code", [1, 2])
def test_failed_or_noop_race_week_does_not_build_marts(ingest_code):
    module = runner()
    with (
        patch.object(module, "FileLock"),
        patch.object(
            module.subprocess, "run", return_value=MagicMock(returncode=ingest_code)
        ) as run,
        pytest.raises(SystemExit) as error,
    ):
        module.main()
    assert error.value.code == (0 if ingest_code == 2 else ingest_code)
    assert run.call_count == 1


def test_successful_or_partial_race_week_builds_marts():
    module = runner()
    with (
        patch.object(module, "FileLock"),
        patch.object(
            module.subprocess, "run", side_effect=[MagicMock(returncode=0), MagicMock(returncode=0)]
        ) as run,
        pytest.raises(SystemExit) as error,
    ):
        module.main()
    assert error.value.code == 0
    assert run.call_count == 2
    assert "build" in run.call_args.args[0]
