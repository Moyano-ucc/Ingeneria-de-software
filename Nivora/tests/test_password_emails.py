"""Password recovery and password change e-mails (E03, E04)."""

import re
import smtplib

import pytest

from app import create_app
from config import TestingConfig
from services import email_service
from services.email_service import EmailService
from tests.test_app import test_client


class SmtpConfig(TestingConfig):
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USERNAME = "nivora@example.com"
    SMTP_PASSWORD = "abcd efgh ijkl mnop"
    SMTP_FROM = None
    SMTP_USE_TLS = True
    SMTP_USE_SSL = False
    PUBLIC_BASE_URL = None
    PASSWORD_RESET_TOKEN_TTL = 3600


class FakeSMTP:
    sent = []
    logins = []
    fail_login = False

    def __init__(self, host, port, timeout=None, context=None):
        self.host, self.port = host, port

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context=None):
        pass

    def login(self, user, password):
        if FakeSMTP.fail_login:
            raise smtplib.SMTPAuthenticationError(535, b"bad credentials")
        FakeSMTP.logins.append((user, password))

    def send_message(self, message):
        FakeSMTP.sent.append(message)
        return {}


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("NIVORA_DATABASE_PATH", str(tmp_path / "nivora.db"))
    FakeSMTP.sent, FakeSMTP.logins, FakeSMTP.fail_login = [], [], False
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(email_service.smtplib, "SMTP_SSL", FakeSMTP)


def _csrf(client):
    html = client.get("/recuperar-contrasena").text
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def _register(client, email="ana@example.com", password="clave-segura-1"):
    client.get("/registro")
    client.post(
        "/registro",
        data={
            "csrf_token": _csrf(client),
            "nombre": "Ana",
            "email": email,
            "password": password,
            "confirmacion": password,
        },
    )


def _link_from_last_email():
    body = FakeSMTP.sent[-1].get_body(("plain",)).get_content()
    return re.search(r"https?://\S+/restablecer-contrasena/\S+", body).group(0)


def test_recovery_sends_a_real_email_and_the_link_resets_the_password():
    client = test_client(create_app(SmtpConfig))
    _register(client)
    client.post("/logout", data={"csrf_token": _csrf(client)})
    client.headers.update({"x-forwarded-host": "nivora-8000.app.github.dev", "x-forwarded-proto": "https"})

    response = client.post(
        "/recuperar-contrasena", data={"csrf_token": _csrf(client), "email": "ANA@example.com"}
    )

    assert response.status_code == 200
    assert "te enviamos un enlace" in response.text
    assert "Enlace de prueba" not in response.text and "Modo desarrollo" not in response.text
    assert len(FakeSMTP.sent) == 1
    message = FakeSMTP.sent[0]
    assert message["To"] == "ana@example.com"
    assert message["From"] == "Nivora <nivora@example.com>"
    assert FakeSMTP.logins == [("nivora@example.com", "abcdefghijklmnop")]
    link = _link_from_last_email()
    assert link.startswith("https://nivora-8000.app.github.dev/restablecer-contrasena/")

    path = link.split("app.github.dev")[1]
    assert "Crear contraseña nueva" in client.get(path).text
    reset = client.post(
        path,
        data={"csrf_token": _csrf(client), "password": "otra-clave-2", "confirmacion": "otra-clave-2"},
    )
    assert "Contraseña actualizada" in reset.text

    login = client.post(
        "/login",
        data={"csrf_token": _csrf(client), "email": "ana@example.com", "password": "otra-clave-2"},
    )
    assert login.headers["Location"] == "/aprender"

    reused = client.get(path)
    assert reused.status_code == 400
    assert "Enlace no válido" in reused.text


def test_unknown_email_gets_the_same_answer_without_sending_anything():
    client = test_client(create_app(SmtpConfig))

    response = client.post(
        "/recuperar-contrasena", data={"csrf_token": _csrf(client), "email": "nadie@example.com"}
    )

    assert response.status_code == 200
    assert "te enviamos un enlace" in response.text
    assert FakeSMTP.sent == []


def test_smtp_failure_is_reported_honestly():
    client = test_client(create_app(SmtpConfig))
    _register(client)
    FakeSMTP.fail_login = True

    response = client.post(
        "/recuperar-contrasena", data={"csrf_token": _csrf(client), "email": "ana@example.com"}
    )

    assert response.status_code == 503
    assert "No pudimos enviar el correo" in response.text
    assert "te enviamos un enlace" not in response.text


def test_invalid_email_is_rejected_inline():
    client = test_client(create_app(SmtpConfig))

    response = client.post(
        "/recuperar-contrasena", data={"csrf_token": _csrf(client), "email": "no-es-correo"}
    )

    assert response.status_code == 400
    assert "Introduce un correo electrónico válido" in response.text


def test_change_password_from_settings_emails_the_account_owner():
    client = test_client(create_app(SmtpConfig))
    _register(client)

    response = client.post("/ajustes/cambiar-contrasena", data={"csrf_token": _csrf(client)})
    assert response.status_code == 303
    assert response.headers["Location"] == "/ajustes"
    settings = client.get("/ajustes").text

    assert "Te enviamos un correo a ana@example.com" in settings
    assert FakeSMTP.sent[-1]["Subject"] == "Cambia tu contraseña de Nivora"
    assert "Hola Ana" in FakeSMTP.sent[-1].get_body(("plain",)).get_content()
    # The feedback is shown only once.
    assert "Te enviamos un correo" not in client.get("/ajustes").text


def test_change_password_without_smtp_explains_the_problem():
    class NoSmtp(SmtpConfig):
        SMTP_HOST = None

    client = test_client(create_app(NoSmtp))
    _register(client)
    client.post("/ajustes/cambiar-contrasena", data={"csrf_token": _csrf(client)})
    settings = client.get("/ajustes").text

    assert "no está configurado" in settings
    assert "Te enviamos un correo" not in settings
    assert FakeSMTP.sent == []


def test_change_password_requires_login():
    client = test_client()
    response = client.post("/ajustes/cambiar-contrasena", data={"csrf_token": _csrf(client)})
    assert response.headers["Location"] == "/login"


def test_expired_or_unknown_token_is_detected_before_showing_the_form():
    client = test_client(create_app(SmtpConfig))
    response = client.get("/restablecer-contrasena/token-inventado")

    assert response.status_code == 400
    assert "Solicitar un enlace nuevo" in response.text


def test_email_service_reports_missing_settings_and_uses_ssl_on_port_465():
    class Empty:
        SMTP_HOST = None

    assert EmailService(Empty).missing_settings() == [
        "NIVORA_SMTP_HOST",
        "NIVORA_SMTP_USERNAME",
        "NIVORA_SMTP_PASSWORD",
        "NIVORA_SMTP_FROM",
    ]
    assert EmailService(Empty).send("a@b.com", "s", "t").error == "not_configured"

    class Ssl(SmtpConfig):
        SMTP_PORT = 465

    assert EmailService(Ssl).use_ssl is True
    assert EmailService(SmtpConfig).use_ssl is False
