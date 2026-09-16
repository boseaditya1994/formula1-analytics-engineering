import importlib.util
from pathlib import Path
from unittest.mock import MagicMock


def load_module():
    path = Path(__file__).resolve().parents[1] / "scripts/export_dashboard_data.py"
    spec = importlib.util.spec_from_file_location("export_dashboard_data", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_export_writes_header_and_rows(tmp_path):
    module = load_module()
    cursor = MagicMock()
    cursor.description = [("A",), ("B",)]
    cursor.fetchall.return_value = [(1, "x"), (2, "y")]
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor

    count = module.export(connection, "sample", "select 1", tmp_path)

    assert count == 2
    contents = (tmp_path / "sample.csv").read_text(encoding="utf-8").splitlines()
    assert contents == ["A,B", "1,x", "2,y"]
