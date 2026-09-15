from unittest.mock import MagicMock

import pytest

from f1_pipeline.loader import load


def connection_with_counts(counts):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.side_effect = counts
    return connection, cursor


def test_reconciliation_failure_rolls_back():
    connection, cursor = connection_with_counts([(0,), (1, 0), (2,)])
    with pytest.raises(ValueError, match="count mismatch"):
        load(connection, "run", "results", 2025, 1, [{}])
    commands = [call.args[0] for call in cursor.execute.call_args_list]
    assert commands[-1] == "ROLLBACK"
    assert "COMMIT" not in commands


def test_duplicate_target_prevents_merge():
    connection, cursor = connection_with_counts([(1,)])
    with pytest.raises(ValueError, match="duplicate"):
        load(connection, "run", "results", 2025, 1, [{}])
    assert not any("MERGE" in call.args[0] for call in cursor.execute.call_args_list)


def test_no_change_counts_and_commit():
    connection, cursor = connection_with_counts([(0,), (0, 0), (1,), (1,)])
    stats = load(connection, "run", "results", 2025, 1, [{}])
    assert stats == {"received": 1, "inserted": 0, "updated": 0, "unchanged": 1, "raw_count": 1}
    assert cursor.execute.call_args.args[0] == "COMMIT"
