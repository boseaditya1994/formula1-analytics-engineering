"""Export analytics marts to CSV extracts for Tableau Public (extract-only, no live connection).

Example: uv run --frozen python scripts/export_dashboard_data.py --profile-file PATH
Reads with the F1_BI_READER role; never writes credentials to the output files.
"""

import argparse
import csv
from pathlib import Path

from f1_pipeline.connection import connect

QUERIES = {
    "driver_race_performance": """
        select p.*, r.circuit_name, r.country
        from F1_ANALYTICS.MARTS.DRIVER_RACE_PERFORMANCE p
        join F1_ANALYTICS.MARTS.DIM_RACE r
          on p.season = r.season and p.round_number = r.round_number
        order by p.season, p.round_number, p.finishing_position
    """,
    "driver_championship_progression": """
        select *
        from F1_ANALYTICS.MARTS.DRIVER_CHAMPIONSHIP_PROGRESSION
        order by season, round_number, championship_position
    """,
    "constructor_championship_progression": """
        select *
        from F1_ANALYTICS.MARTS.CONSTRUCTOR_CHAMPIONSHIP_PROGRESSION
        order by season, round_number, championship_position
    """,
}


def export(connection, name: str, sql: str, out_dir: Path) -> int:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        columns = [c[0] for c in cursor.description]
        rows = cursor.fetchall()
    out_path = out_dir / f"{name}.csv"
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile-file", type=Path)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "dashboards" / "tableau" / "data",
    )
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    connection = connect(args.profile_file, role="F1_BI_READER", schema="MARTS")
    try:
        for name, sql in QUERIES.items():
            count = export(connection, name, sql, args.out_dir)
            print(f"{name}: {count} rows -> {args.out_dir / (name + '.csv')}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
