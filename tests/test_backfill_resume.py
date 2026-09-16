from pathlib import Path
from unittest.mock import MagicMock, patch

from f1_pipeline.ingestion import backfill


def test_resume_skips_only_successful_closed_season_partition():
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value.fetchone.return_value = ("SUCCESS",)
    with (
        patch("f1_pipeline.ingestion.FileLock"),
        patch("f1_pipeline.ingestion.connect") as connect,
        patch("f1_pipeline.ingestion.open_client"),
        patch("f1_pipeline.ingestion.loader.initialize"),
        patch("f1_pipeline.ingestion.run_partition") as run,
    ):
        connect.return_value.__enter__.return_value = connection
        backfill(2018, 2018, ["results"], None, None, root=Path.cwd(), resume=True)
        run.assert_not_called()


def test_failed_checkpoint_is_retried():
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value.fetchone.return_value = ("FAILED",)
    with (
        patch("f1_pipeline.ingestion.FileLock"),
        patch("f1_pipeline.ingestion.connect") as connect,
        patch("f1_pipeline.ingestion.open_client"),
        patch("f1_pipeline.ingestion.loader.initialize"),
        patch("f1_pipeline.ingestion.run_partition") as run,
    ):
        connect.return_value.__enter__.return_value = connection
        backfill(2018, 2018, ["results"], None, None, root=Path.cwd(), resume=True)
        run.assert_called_once()


def test_resume_never_skips_current_season():
    from datetime import UTC, datetime

    year = datetime.now(UTC).year
    with (
        patch("f1_pipeline.ingestion.FileLock"),
        patch("f1_pipeline.ingestion.connect"),
        patch("f1_pipeline.ingestion.open_client"),
        patch("f1_pipeline.ingestion.loader.initialize"),
        patch("f1_pipeline.ingestion.run_partition") as run,
    ):
        backfill(year, year, ["results"], None, None, root=Path.cwd(), resume=True)
        run.assert_called_once()
