"""Build twice and compare fact row counts and unordered content fingerprints.

The first build must already have completed. This script captures the existing
fact state, executes a normal incremental dbt build and verifies the state again.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from f1_pipeline.connection import connect

FACTS = {
    "FCT_RACE_RESULTS": "RESULT_KEY",
    "FCT_QUALIFYING_RESULTS": "QUALIFYING_KEY",
    "FCT_SPRINT_RESULTS": "SPRINT_KEY",
    "FCT_DRIVER_STANDINGS": "STANDING_KEY",
    "FCT_CONSTRUCTOR_STANDINGS": "STANDING_KEY",
}


def snapshot(profile: Path) -> dict:
    state = {}
    with connect(profile) as connection, connection.cursor() as cursor:
        cursor.execute("USE ROLE F1_TRANSFORMER")
        for table, key in FACTS.items():
            cursor.execute(
                f"SELECT COUNT(*), COUNT(DISTINCT {key}), HASH_AGG(*) "
                f"FROM F1_ANALYTICS.MARTS.{table}"
            )
            count, unique, fingerprint = cursor.fetchone()
            if count != unique:
                raise ValueError("Duplicate fact keys")
            state[table] = {
                "rows": int(count),
                "unique_keys": int(unique),
                "fingerprint": str(fingerprint),
            }
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-file", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    before = snapshot(args.profile_file)
    print(json.dumps({"before": before}), flush=True)
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/run_dbt.py"),
            "build",
            "--profile-file",
            str(args.profile_file),
            "--quiet",
        ],
        check=True,
    )
    after = snapshot(args.profile_file)
    if before != after:
        raise ValueError("Fact state changed during unchanged-source incremental rebuild")
    results = json.loads((root / "dbt_f1/target/run_results.json").read_text())
    report = {
        "incremental_idempotency": "passed",
        "facts": after,
        "dbt_invocation_id": results["metadata"]["invocation_id"],
        "dbt_elapsed_seconds": results["elapsed_time"],
        "dbt_status_counts": {
            status: sum(item["status"] == status for item in results["results"])
            for status in sorted({item["status"] for item in results["results"]})
        },
    }
    output = root / "artifacts/incremental_verification.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "FAILED",
                    "error_type": type(exc).__name__,
                    "error_code": getattr(exc, "errno", None),
                }
            ),
            flush=True,
        )
        raise SystemExit(1) from None
