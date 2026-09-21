"""Formula 1 historical ingestion and local runtime diagnostics."""

import argparse
import json
import platform
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor")
    daily_parser = commands.add_parser(
        "daily", help="Refresh current schedules and recent/gap data"
    )
    daily_parser.add_argument("--profile-file", type=Path)
    daily_parser.add_argument("--lookback-days", type=int, default=14)
    race_week_parser = commands.add_parser(
        "race-week", help="Refresh published data for the imminent/current race only"
    )
    race_week_parser.add_argument("--profile-file", type=Path)
    race_week_parser.add_argument("--season", type=int, default=datetime.now(UTC).year)
    race_week_parser.add_argument("--window-days", type=int, default=2)
    historical = commands.add_parser("backfill", help="Load historical Jolpica partitions")
    historical.add_argument("--start-season", type=int, required=True)
    historical.add_argument("--end-season", type=int)
    historical.add_argument("--round", type=int)
    historical.add_argument(
        "--resume", action="store_true", help="Skip successful closed-season partition checkpoints"
    )
    historical.add_argument(
        "--datasets",
        nargs="+",
        default=[
            "races",
            "results",
            "qualifying",
            "sprint",
            "driverstandings",
            "constructorstandings",
        ],
        choices=[
            "races",
            "results",
            "qualifying",
            "sprint",
            "driverstandings",
            "constructorstandings",
        ],
    )
    historical.add_argument(
        "--profile-file",
        type=Path,
        help="Explicit local dbt credential file; never printed or modified",
    )
    args = parser.parse_args()
    if args.command == "daily":
        from f1_pipeline.daily import daily

        if not 1 <= args.lookback_days <= 90:
            parser.error("lookback-days must be between 1 and 90")
        try:
            report = daily(args.profile_file, root=Path.cwd(), lookback_days=args.lookback_days)
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "status": "FAILED",
                        "error_type": type(exc).__name__,
                        "error_code": getattr(exc, "errno", None),
                    }
                )
            )
            raise SystemExit(1) from None
        raise SystemExit(0 if report["status"] == "SUCCESS" else 2)
    if args.command == "race-week":
        from f1_pipeline.race_week import race_week

        if not 0 <= args.window_days <= 3:
            parser.error("window-days must be between 0 and 3")
        try:
            report = race_week(
                args.profile_file,
                root=Path.cwd(),
                season=args.season,
                window_days=args.window_days,
            )
        except Exception as exc:
            print(json.dumps({"status": "FAILED", "error_type": type(exc).__name__}))
            raise SystemExit(1) from None
        print(json.dumps(report), flush=True)
        raise SystemExit(0 if report["status"] in ("SUCCESS", "PARTIAL") else 2)
    if args.command == "backfill":
        from f1_pipeline.ingestion import backfill

        end = args.end_season if args.end_season is not None else datetime.now(UTC).year - 1
        if not 1950 <= args.start_season <= end <= datetime.now(UTC).year:
            parser.error("Require 1950 <= start-season <= end-season <= current year")
        if args.round is not None and (args.round < 1 or args.start_season != end):
            parser.error("A round requires one season and a positive round number")
        try:
            backfill(
                args.start_season,
                end,
                list(dict.fromkeys(args.datasets)),
                args.round,
                args.profile_file,
                root=Path.cwd(),
                resume=args.resume,
            )
        except Exception as exc:
            # Connector errors can contain identifiers; expose only a safe classification.
            print(
                json.dumps(
                    {
                        "status": "FAILED",
                        "error_type": type(exc).__name__,
                        "error_code": getattr(exc, "errno", None),
                    }
                )
            )
            raise SystemExit(1) from None
        return
    packages = (
        "f1-analytics-engineering",
        "dbt-core",
        "dbt-snowflake",
        "snowflake-connector-python",
        "httpx",
    )
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "packages": {name: version(name) for name in packages},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
