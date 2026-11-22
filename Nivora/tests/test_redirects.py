"""Redirects must keep the domain the browser is using (E01).

Behind the GitHub Codespaces proxy Uvicorn receives ``Host: localhost:8000``.
An absolute ``Location`` built from that header sends the browser to
``localhost`` and fails with ERR_CONNECTION_REFUSED, so every redirect must be
relative.
"""

import re

import pytest

from tests.test_app import test_client


PROXY_HEADERS = {
    "host": "localhost:8000",
    "x-forwarded-host": "nivora-8000.app.github.dev",
    "x-forwarded-proto": "https",
}


@pytest.fixture(autouse=True)
def isolate_database(tmp_path, monkeypatch):
    monkeypatch.setenv("NIVORA_DATABASE_PATH", str(tmp_path / "nivora.db"))


def _csrf(client):
    html = client.get("/recuperar-contrasena").text
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def _assert_relative(response, expected_path):
    location = response.headers["Location"]
    assert location.startswith("/"), location
    assert "localhost" not in location
    assert location.split("?")[0] == expected_path


def test_full_flow_behind_proxy_never_redirects_to_localhost():
    client = test_client()
    client.headers.update(PROXY_HEADERS)

    client.get("/registro")
    registro = client.post(
        "/registro",
        data={
            "csrf_token": _csrf(client),
            "nombre": "Ana",
            "email": "ana@example.com",
            "password": "clave-segura-1",
            "confirmacion": "clave-segura-1",
        },
    )
    _assert_relative(registro, "/nivel")

    nivel = client.post(
        "/nivel",
        data={"csrf_token": _csrf(client), "nivel_inicial": "no_se_nada"},
    )
    _assert_relative(nivel, "/aprender")
    assert client.get("/aprender").status_code == 200

    for lesson_id, answers in (
        ("variables", ["nombre", "int", "True"]),
        ("operadores", ["7", "True", "=="]),
    ):
        quiz = client.post(
            f"/aprender/leccion/{lesson_id}/completar",
            data={
                "csrf_token": _csrf(client),
                **{f"respuesta_{i}": a for i, a in enumerate(answers, 1)},
            },
        )
        _assert_relative(quiz, f"/aprender/leccion/{lesson_id}")
        assert client.get(quiz.headers["Location"]).status_code == 200

    practice = client.post(
        "/practica",
        data={"csrf_token": _csrf(client), "ejercicio": "variables", "codigo": "edad = 20"},
    )
    _assert_relative(practice, "/practica")

    logout = client.post("/logout", data={"csrf_token": _csrf(client)})
    _assert_relative(logout, "/")

    client.get("/login")
    login = client.post(
        "/login",
        data={
            "csrf_token": _csrf(client),
            "email": "ana@example.com",
            "password": "clave-segura-1",
        },
    )
    _assert_relative(login, "/aprender")

    failed_login = client.post(
        "/login",
        data={"csrf_token": _csrf(client), "email": "x@example.com", "password": "nope-1234"},
    )
    _assert_relative(failed_login, "/login")


def test_protected_routes_redirect_relatively_to_login():
    client = test_client()
    client.headers.update(PROXY_HEADERS)

    for path in ("/aprender", "/progreso", "/practica", "/ajustes", "/aprender/leccion/variables"):
        response = client.get(path)
        assert response.status_code in (302, 303)
        _assert_relative(response, "/login")


def test_templates_do_not_render_absolute_internal_urls():
    client = test_client()
    client.headers.update(PROXY_HEADERS)

    for path in ("/", "/login", "/registro", "/recuperar-contrasena"):
        html = client.get(path).text
        assert not re.search(r'(href|action|src)="https?://localhost', html)
