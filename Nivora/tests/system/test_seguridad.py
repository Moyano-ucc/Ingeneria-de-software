"""Security tests (non-functional): CSRF, sessions, access control and injection."""

import re

import pytest
from fastapi.testclient import TestClient

from app import create_app
from config import TestingConfig
from database.database import DatabaseConnection
from tests.helpers import csrf_from_page, logged_in_client, login, register_user, test_client

pytestmark = pytest.mark.security


def test_post_without_csrf_is_rejected():
    client = test_client()
    response = client.post("/login", data={"email": "a@b.com", "password": "password-123"})

    assert response.status_code == 400


def test_app_keeps_stable_session_cookie_name_and_configured_secret():
    from app import create_app
    from config import Config

    class ProductionConfig(Config):
        TESTING = False
        SECRET_KEY = "secreto-estable"

    app = create_app(ProductionConfig)

    assert app.state.settings.SECRET_KEY == "secreto-estable"
    assert app.state.session_cookie == "nivora_session"


def test_session_cookie_expires_after_fifteen_minutes():
    response = test_client().get("/login")

    assert "max-age=900" in response.headers["set-cookie"].lower()


# Every form that changes state must require the CSRF token.
STATE_CHANGING_POSTS = [
    "/login",
    "/registro",
    "/nivel",
    "/logout",
    "/recuperar-contrasena",
    "/ajustes/cambiar-contrasena",
    "/verificar-codigo",
    "/aprender/leccion/variables/completar",
    "/practica",
]


@pytest.mark.parametrize("path", STATE_CHANGING_POSTS)
def test_every_form_rejects_requests_without_csrf(path):
    client = logged_in_client(progreso={})

    response = client.post(path, data={"email": "ana@example.com"})

    assert response.status_code == 400
    assert "Token CSRF inválido" in response.text


def test_a_rejected_csrf_request_has_no_side_effects():
    client = logged_in_client(progreso={})
    client.post("/aprender/leccion/variables/completar", data={"csrf_token": "falso", "respuesta_1": "nombre"})

    with client.session_transaction() as session:
        assert "variables" not in session.get("progreso", {})


PROTECTED_PAGES = [
    "/aprender",
    "/aprender/ruta/01",
    "/aprender/leccion/variables",
    "/practica",
    "/progreso",
    "/ajustes",
    "/certificado",
]


@pytest.mark.parametrize("path", PROTECTED_PAGES)
def test_protected_pages_require_a_session(path):
    response = test_client().get(path)

    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_sql_injection_in_login_does_not_authenticate():
    client = test_client()
    register_user(client)
    client.post("/logout", data={"csrf_token": csrf_from_page(client)})

    response = login(client, email="' OR '1'='1' --", password="' OR '1'='1")

    assert response.headers["Location"] == "/login"
    assert client.get("/aprender").headers["Location"] == "/login"


def test_user_supplied_names_are_escaped_in_html():
    client = test_client()
    register_user(client, nombre="<script>alert(1)</script>")

    html = client.get("/ajustes").text

    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_passwords_are_stored_hashed_never_in_plain_text():
    client = test_client()
    register_user(client, password="clave-segura-1")

    connection = DatabaseConnection().connect()
    try:
        stored = connection.execute("SELECT contrasena FROM PERSONA").fetchone()[0]
    finally:
        connection.close()

    assert stored != "clave-segura-1"
    assert stored.startswith(("scrypt:", "pbkdf2:"))


def test_security_headers_and_no_cache_on_html():
    response = test_client().get("/login")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Cache-Control"] == "no-store, max-age=0"


def test_session_cookie_is_http_only_and_same_site():
    response = test_client().get("/login")
    cookie = response.headers["set-cookie"].lower()

    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_password_reset_code_is_stored_as_a_hash(monkeypatch):
    client = test_client()
    register_user(client)
    client.post("/recuperar-contrasena", data={"csrf_token": csrf_from_page(client), "email": "ana@example.com"})
    page = client.get("/verificar-codigo").text
    code = re.search(r"Tu código de prueba es <strong>(\d{6})</strong>", page).group(1)

    connection = DatabaseConnection().connect()
    try:
        stored = connection.execute("SELECT token_hash FROM PASSWORD_RESET").fetchone()[0]
    finally:
        connection.close()

    assert code not in stored
    assert len(stored) == 64


def test_internal_errors_show_a_generic_message_without_details():
    app = create_app(TestingConfig)

    @app.get("/fallo-de-prueba")
    def failing_page():
        raise RuntimeError("detalle interno secreto")

    @app.get("/api/fallo-de-prueba")
    def failing_api():
        raise RuntimeError("detalle interno secreto")

    client = TestClient(app, raise_server_exceptions=False)
    page = client.get("/fallo-de-prueba")
    api = client.get("/api/fallo-de-prueba")

    assert page.status_code == 500 and "Ocurrió un error interno" in page.text
    assert api.status_code == 500 and api.json() == {"detail": "Ocurrió un error interno"}
    assert "secreto" not in page.text + api.text
