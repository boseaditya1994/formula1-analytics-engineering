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
    connection,
    client: JolpicaClient,
    dataset: str,
    season: int,
    race: int | None = None,
    *,
    rows: list[dict] | None = None,
    allow_pending: bool = False,
) -> dict:
    run_id = str(uuid.uuid4())
    started = time.monotonic()
    loader.start(connection, run_id, dataset, season, race)
    try:
        if rows is None:
            rows = client.fetch(dataset, season, race)
        if not rows and allow_pending:
            # Never advance success or reconcile an unpublished required partition as complete.
            with connection.cursor() as q:
                q.execute(
                    """UPDATE F1_ANALYTICS.AUDIT.INGESTION_RUNS
                    SET STATUS='PENDING', COMPLETED_AT=CURRENT_TIMESTAMP(), RECORDS_RECEIVED=0
                    WHERE RUN_ID=%s""",
                    (run_id,),
                )
            result = {
                "run_id": run_id,
                "dataset": dataset,
                "season": season,
                "round": race,
                "status": "PENDING",
            }
            print(json.dumps(result), flush=True)
            return result
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
    start: int,
    end: int,
    datasets: list[str],
    race: int | None,
    profile: Path | None,
    *,
    root: Path,
    resume: bool = False,
) -> None:
    # Remote orchestration must also use one concurrency group. This lock only protects this host.
    with FileLock(str(root / ".pipeline.lock"), timeout=0):
        with connect(profile) as connection, open_client() as http:
            loader.initialize(connection, root / "snowflake/objects/01_ingestion.sql")
            client = JolpicaClient(http)

            def ingest(dataset: str, season: int, number: int | None) -> None:
                if resume and season < datetime.now(UTC).year:
                    with connection.cursor() as q:
                        q.execute(
                            """SELECT STATUS FROM F1_ANALYTICS.AUDIT.INGESTION_RUNS
                            WHERE DATASET=%s AND SEASON=%s
                              AND COALESCE(ROUND_NUMBER,0)=COALESCE(%s,0)
                            ORDER BY STARTED_AT DESC LIMIT 1""",
                            (dataset, season, number),
                        )
                        latest = q.fetchone()
                    if latest and latest[0] == "SUCCESS":
                        print(
                            json.dumps(
                                {
                                    "dataset": dataset,
                                    "season": season,
                                    "round": number,
                                    "status": "SKIPPED_CHECKPOINT",
                                }
                            ),
                            flush=True,
                        )
                        return
                run_partition(connection, client, dataset, season, number)

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
                            ingest(dataset, season, number)
                    else:
                        ingest(dataset, season, race)
