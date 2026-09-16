"""Run daily ingestion followed by dbt build; propagate failures and pending data."""

import argparse
import subprocess
import sys
from pathlib import Path

from filelock import FileLock


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-file", type=Path)
    parser.add_argument("--lookback-days", type=int, default=14)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    profile = ["--profile-file", str(args.profile_file.resolve())] if args.profile_file else []
    # Keep overlapping daily pipeline invocations from mixing ingestion/build phases.
    with FileLock(str(root / ".daily_pipeline.lock"), timeout=0):
        ingest = subprocess.run(
            [
                sys.executable,
                "-m",
                "f1_pipeline",
                "daily",
                "--lookback-days",
                str(args.lookback_days),
                *profile,
            ],
            cwd=root,
            check=False,
        )
        if ingest.returncode:
            raise SystemExit(ingest.returncode)
        build = subprocess.run(
            [sys.executable, str(root / "scripts/run_dbt.py"), "build", *profile],
            cwd=root,
            check=False,
        )
        raise SystemExit(build.returncode)


if __name__ == "__main__":
    main()
