from datetime import date
from unittest.mock import MagicMock

import pytest

from f1_pipeline.daily import DATASETS, seasons_for, select_partitions
from f1_pipeline.ingestion import run_partition


def schedule():
    return [
        {"round": str(i), "date": f"2026-06-{i * 5:02}", **({"Sprint": {}} if i == 2 else {})}
        for i in range(1, 5)
    ]


def test_unchanged_history_is_skipped_but_latest_two_rechecked():
    covered = {(d, r) for d in DATASETS for r in range(1, 5)}
    plan = select_partitions(schedule(), covered, date(2026, 8, 1), 14)
    assert {r for _, r in plan} == {3, 4}
    assert len(plan) == 8


def test_missing_older_partition_recovered_without_redownloading_other_history():
    covered = {(d, r) for d in DATASETS for r in range(1, 5)} - {("qualifying", 1)}
    plan = select_partitions(schedule(), covered, date(2026, 8, 1), 14)
    assert ("qualifying", 1) in plan
    assert ("results", 1) not in plan


def test_correction_window_includes_more_than_latest_two():
    covered = {(d, r) for d in DATASETS for r in range(1, 5)}
    plan = select_partitions(schedule(), covered, date(2026, 6, 21), 14)
    assert {r for _, r in plan} == {2, 3, 4}
    assert ("sprint", 2) in plan
    assert ("sprint", 3) not in plan


def test_today_and_future_races_are_not_required():
    plan = select_partitions(schedule(), set(), date(2026, 6, 10), 14)
    assert {r for _, r in plan} == {1}


def test_new_year_keeps_previous_season_in_window():
    assert seasons_for(date(2027, 1, 5), 14) == [2026, 2027]
    assert seasons_for(date(2027, 2, 1), 14) == [2027]


def test_empty_required_daily_partition_does_not_merge_or_advance_success():
    connection = MagicMock()
    client = MagicMock()
    client.fetch.return_value = []
    result = run_partition(connection, client, "results", 2026, 1, allow_pending=True)
    assert result["status"] == "PENDING"
    q = connection.cursor.return_value.__enter__.return_value
    statements = [c.args[0] for c in q.execute.call_args_list]
    assert not any("MERGE" in sql or "'SUCCESS'" in sql for sql in statements)
    assert any("'PENDING'" in sql for sql in statements)


def test_empty_historical_results_still_fail():
    from f1_pipeline.api import SourceError

    client = MagicMock()
    client.fetch.return_value = []
    with pytest.raises(SourceError):
        run_partition(MagicMock(), client, "results", 2025, 1)
