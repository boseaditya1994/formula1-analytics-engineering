"""Refresh the active race only, then build dbt when source data changed."""

import subprocess
import sys
from pathlib import Path

from filelock import FileLock


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    with FileLock(str(root / ".race_week_pipeline.lock"), timeout=0):
        ingest = subprocess.run(
            [sys.executable, "-m", "f1_pipeline", "race-week"], cwd=root, check=False
        )
        if ingest.returncode == 2:
            # No active race or no published source result is an expected, observable no-op.
            raise SystemExit(0)
        if ingest.returncode:
            raise SystemExit(ingest.returncode)
        build = subprocess.run(
            [sys.executable, str(root / "scripts/run_dbt.py"), "build"], cwd=root, check=False
        )
        raise SystemExit(build.returncode)


if __name__ == "__main__":
    main()
