"""Bounded current-race refresh for race-week source publication."""

from datetime import UTC, date, datetime
from pathlib import Path

from filelock import FileLock

from f1_pipeline import loader
from f1_pipeline.api import JolpicaClient, SourceError, open_client
from f1_pipeline.connection import connect
from f1_pipeline.ingestion import run_partition

DATASETS = ("qualifying", "sprint", "results", "driverstandings", "constructorstandings")


def active_race(schedule: list[dict], today: date, window_days: int) -> dict | None:
    """Select the nearest race whose Sunday falls within the bounded race-week window."""
    eligible = [
        race
        for race in schedule
        if 0 <= (date.fromisoformat(race["date"]) - today).days <= window_days
    ]
    return min(eligible, key=lambda race: (race["date"], int(race["round"])), default=None)


def race_week(
    profile: Path | None,
    *,
    root: Path,
    season: int,
    window_days: int = 2,
    today: date | None = None,
) -> dict:
    """Refresh one imminent/current race, preserving PENDING source-publication evidence."""
    current_day = today or datetime.now(UTC).date()
    with FileLock(str(root / ".pipeline.lock"), timeout=0):
        with connect(profile) as connection, open_client() as http:
            loader.initialize(connection, root / "snowflake/objects/01_ingestion.sql")
            client = JolpicaClient(http)
            schedule = client.fetch("races", season)
            if not schedule:
                raise SourceError("Current season schedule is empty")
            race = active_race(schedule, current_day, window_days)
            if race is None:
                return {"status": "NO_ACTIVE_RACE", "season": season, "partitions": 0}
            number = int(race["round"])
            datasets = [dataset for dataset in DATASETS if dataset != "sprint" or "Sprint" in race]
            results = [
                run_partition(connection, client, dataset, season, number, allow_pending=True)
                for dataset in datasets
            ]
            successes = sum(result["status"] == "SUCCESS" for result in results)
            pending = sum(result["status"] == "PENDING" for result in results)
            status = "SUCCESS" if pending == 0 else "PARTIAL" if successes else "PENDING"
            return {
                "status": status,
                "season": season,
                "round": number,
                "race_name": race.get("raceName"),
                "partitions": len(results),
                "successful_partitions": successes,
                "pending_partitions": pending,
            }
