import re

import pytest


@pytest.fixture(autouse=True)
def isolate_database(tmp_path, monkeypatch):
    """Every test uses its own SQLite file; database/nivora.db is never touched."""
    monkeypatch.setenv("NIVORA_DATABASE_PATH", str(tmp_path / "nivora.db"))


def csrf_from_page(client):
    """Read the CSRF token from a rendered form (works with any Host header)."""
    html = client.get("/recuperar-contrasena").text
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
