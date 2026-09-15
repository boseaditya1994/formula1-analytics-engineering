"""Check the installed entry point and diagnostic output contract."""

import json
import subprocess
import sys


def test_doctor_reports_runtime_without_credentials():
    result = subprocess.run(
        [sys.executable, "-m", "f1_pipeline", "doctor"],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    assert report["python"].startswith("3.12.")
    assert set(report) == {"python", "packages"}
    assert report["packages"]["dbt-snowflake"]


def test_backfill_requires_explicit_start_season():
    result = subprocess.run(
        [sys.executable, "-m", "f1_pipeline", "backfill"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "--start-season" in result.stderr
