"""Historical partitions with per-partition audit and a local single-writer lock."""

import json
import time
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

from filelock import FileLock

from f1_pipeline import loader
from f1_pipeline.api import JolpicaClient, SourceError, open_client
from f1_pipeline.connection import connect
from f1_pipeline.records import prepare


def run_partition(
    connection, client: JolpicaClient, dataset: str, season: int, race: int | None = None
) -> dict:
    run_id = str(uuid.uuid4())
    started = time.monotonic()
    loader.start(connection, run_id, dataset, season, race)
    try:
        rows = client.fetch(dataset, season, race)
        if not rows and dataset != "sprint":
            raise SourceError("Expected historical partition is empty")
        records = prepare(dataset, season, rows, race)
        stats = loader.load(connection, run_id, dataset, season, race, records)
    except Exception as exc:
        try:
            loader.fail(connection, run_id, type(exc).__name__)
        except Exception:
            print(json.dumps({"run_id": run_id, "audit_update_failed": True}), flush=True)
        print(
            json.dumps(
                {
                    "run_id": run_id,
                    "dataset": dataset,
                    "season": season,
                    "round": race,
                    "status": "FAILED",
                    "error_type": type(exc).__name__,
                }
            ),
            flush=True,
        )
        raise
    result = {
        "run_id": run_id,
        "dataset": dataset,
        "season": season,
        "round": race,
        "status": "SUCCESS",
        "duration_seconds": round(time.monotonic() - started, 3),
        **stats,
    }
    print(json.dumps(result), flush=True)
    return result


def backfill(
    start: int, end: int, datasets: list[str], race: int | None, profile: Path | None, *, root: Path
) -> None:
    # Remote orchestration must also use one concurrency group. This lock only protects this host.
    with FileLock(str(root / ".pipeline.lock"), timeout=0):
        with connect(profile) as connection, open_client() as http:
            loader.initialize(connection, root / "snowflake/objects/01_ingestion.sql")
            client = JolpicaClient(http)
            for season in range(start, end + 1):
                rounds = None
                for dataset in datasets:
                    if dataset.endswith("standings") and race is None:
                        if rounds is None:
                            schedule = client.fetch("races", season)
                            if not schedule:
                                raise SourceError("Historical season schedule is empty")
                            prepare("races", season, schedule)
                            rounds = [
                                int(r["round"])
                                for r in schedule
                                if date.fromisoformat(r["date"]) < datetime.now(UTC).date()
                            ]
                        for number in rounds:
                            run_partition(connection, client, dataset, season, number)
                    else:
                        run_partition(connection, client, dataset, season, race)
