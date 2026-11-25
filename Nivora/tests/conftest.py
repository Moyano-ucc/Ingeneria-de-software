import pathlib

import pytest


LEVELS = {"unit", "integration", "system", "smoke"}


@pytest.fixture(autouse=True)
def isolate_database(tmp_path, monkeypatch):
    """Every test uses its own SQLite file; database/nivora.db is never touched."""
    monkeypatch.setenv("NIVORA_DATABASE_PATH", str(tmp_path / "nivora.db"))


def pytest_collection_modifyitems(items):
    """The folder of a test defines its level (unit, integration, system, smoke)."""
    for item in items:
        for part in pathlib.Path(str(item.fspath)).parts:
            if part in LEVELS:
                item.add_marker(getattr(pytest.mark, part))
