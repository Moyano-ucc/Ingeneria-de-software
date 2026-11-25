import pathlib

import pytest


LEVELS = {"unit", "integration", "system", "smoke"}


@pytest.fixture(autouse=True)
def isolate_database(tmp_path, monkeypatch):
    """Every test uses its own SQLite file; database/nivora.db is never touched."""
    monkeypatch.setenv("NIVORA_DATABASE_PATH", str(tmp_path / "nivora.db"))


class _NoRealSMTP:
    def __init__(self, *args, **kwargs):
        raise AssertionError(
            "Una prueba intentó conectarse a un servidor de correo real. "
            "Usa el servidor falso de tests/system/test_contrasenas.py."
        )


@pytest.fixture(autouse=True)
def block_real_email(monkeypatch):
    """Safety net: no test may send real e-mails (tests that need SMTP replace
    these classes with a fake server in their own fixture)."""
    from services import email_service

    monkeypatch.setattr(email_service.smtplib, "SMTP", _NoRealSMTP)
    monkeypatch.setattr(email_service.smtplib, "SMTP_SSL", _NoRealSMTP)


def pytest_collection_modifyitems(items):
    """The folder of a test defines its level (unit, integration, system, smoke)."""
    for item in items:
        for part in pathlib.Path(str(item.fspath)).parts:
            if part in LEVELS:
                item.add_marker(getattr(pytest.mark, part))
