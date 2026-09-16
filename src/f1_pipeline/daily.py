"""Bounded correction refresh with durable audit checkpoints and gap recovery."""

import json
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from filelock import FileLock

from f1_pipeline import loader
from f1_pipeline.api import JolpicaClient, SourceError, open_client
from f1_pipeline.connection import connect
from f1_pipeline.ingestion import run_partition
from f1_pipeline.records import prepare

DATASETS = ("results", "qualifying", "sprint", "driverstandings", "constructorstandings")


def seasons_for(today: date, lookback_days: int) -> list[int]:
    """Include the preceding season while the correction window crosses New Year."""
    return list(range((today - timedelta(days=lookback_days)).year, today.year + 1))


def select_partitions(
    schedule: list[dict], covered: set[tuple[str, int]], today: date, lookback_days: int
) -> list[tuple[str, int]]:
    # Wait until the day after a race (UTC); absence then remains an observable pending gap.
    past = sorted(
        (r for r in schedule if date.fromisoformat(r["date"]) < today),
        key=lambda r: int(r["round"]),
    )
    recent = {int(r["round"]) for r in past[-2:]}
    cutoff = today - timedelta(days=lookback_days)
    selected = []
    for race in past:
        number = int(race["round"])
        correction = number in recent or date.fromisoformat(race["date"]) >= cutoff
        for dataset in DATASETS:
            if dataset == "sprint" and "Sprint" not in race:
                continue
            if correction or (dataset, number) not in covered:
                selected.append((dataset, number))
    return selected


def daily(profile: Path | None, *, root: Path, lookback_days: int = 14) -> dict:
    today = datetime.now(UTC).date()
    job_id = str(uuid.uuid4())
    results = []
    with FileLock(str(root / ".pipeline.lock"), timeout=0):
        with connect(profile) as connection, open_client() as http:
            loader.initialize(connection, root / "snowflake/objects/01_ingestion.sql")
            loader.initialize(connection, root / "snowflake/objects/02_daily.sql")
            with connection.cursor() as q:
                q.execute(
                    """INSERT INTO F1_ANALYTICS.AUDIT.DAILY_RUNS
                    (RUN_ID, STARTED_AT, STATUS, LOOKBACK_DAYS)
                    VALUES (%s, CURRENT_TIMESTAMP(), 'RUNNING', %s)""",
                    (job_id, lookback_days),
                )
            try:
                client = JolpicaClient(http)
                for season in seasons_for(today, lookback_days):
                    schedule = client.fetch("races", season)
                    if not schedule:
                        raise SourceError("Current season schedule is empty")
                    prepared = prepare("races", season, schedule)
                    # Audit and load the exact schedule used for planning, with no second fetch.
                    results.append(
                        run_partition(connection, client, "races", season, rows=schedule)
                    )
                    with connection.cursor() as q:
                        q.execute(
                            """WITH ingestion_control AS (
                                SELECT DATASET, SEASON,
                                       COALESCE(ROUND_NUMBER, 0) AS PARTITION_ROUND,
                                       STATUS AS LAST_ATTEMPT_STATUS
                                FROM F1_ANALYTICS.AUDIT.INGESTION_RUNS
                                QUALIFY ROW_NUMBER() OVER (
                                  PARTITION BY DATASET, SEASON, COALESCE(ROUND_NUMBER, 0)
                                  ORDER BY STARTED_AT DESC, RUN_ID DESC
                                ) = 1
                            )
                            SELECT DISTINCT DATASET, ROUND_NUMBER
                            FROM F1_ANALYTICS.RAW.SOURCE_RECORDS r WHERE SEASON=%s
                              AND NOT EXISTS (
                                SELECT 1 FROM ingestion_control c
                                WHERE c.DATASET=r.DATASET AND c.SEASON=r.SEASON
                                  AND c.PARTITION_ROUND IN (0, r.ROUND_NUMBER)
                                  AND c.LAST_ATTEMPT_STATUS <> 'SUCCESS'
                              )""",
                            (season,),
                        )
                        covered = {(str(d), int(r)) for d, r in q.fetchall()}
                    plan = select_partitions(schedule, covered, today, lookback_days)
                    print(
                        json.dumps(
                            {
                                "daily_run_id": job_id,
                                "season": season,
                                "schedule_rows": len(prepared),
                                "selected_partitions": len(plan),
                            }
                        ),
                        flush=True,
                    )
                    for dataset, number in plan:
                        results.append(
                            run_partition(
                                connection, client, dataset, season, number, allow_pending=True
                            )
                        )
                pending = sum(r["status"] == "PENDING" for r in results)
                status = "PENDING" if pending else "SUCCESS"
                totals = {
                    name: sum(r.get(name, 0) for r in results)
                    for name in ("received", "inserted", "updated", "unchanged")
                }
                report = {
                    "daily_run_id": job_id,
                    "status": status,
                    "partitions": len(results),
                    "pending_partitions": pending,
                    **totals,
                }
                with connection.cursor() as q:
                    q.execute(
                        """UPDATE F1_ANALYTICS.AUDIT.DAILY_RUNS SET
                        COMPLETED_AT=CURRENT_TIMESTAMP(), STATUS=%s, SUMMARY=PARSE_JSON(%s)
                        WHERE RUN_ID=%s""",
                        (status, json.dumps(report), job_id),
                    )
                print(json.dumps(report), flush=True)
                return report
            except Exception as exc:
                with connection.cursor() as q:
                    q.execute(
                        """UPDATE F1_ANALYTICS.AUDIT.DAILY_RUNS SET STATUS='FAILED',
                        COMPLETED_AT=CURRENT_TIMESTAMP(), ERROR_TYPE=%s WHERE RUN_ID=%s""",
                        (type(exc).__name__, job_id),
                    )
                raise
