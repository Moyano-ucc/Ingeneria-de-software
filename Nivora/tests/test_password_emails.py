"""Password recovery and password change with an e-mailed 6-digit code (E03, E04)."""

import re
import smtplib

import pytest

from app import create_app
from config import TestingConfig
from services import email_service
from services.email_service import EmailService
from tests.conftest import csrf_from_page
from tests.test_app import test_client


class SmtpConfig(TestingConfig):
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USERNAME = "nivora@example.com"
    SMTP_PASSWORD = "abcd efgh ijkl mnop"
    SMTP_FROM = None
    SMTP_USE_TLS = True
    SMTP_USE_SSL = False
    PASSWORD_RESET_TOKEN_TTL = 900


class ProductionLikeConfig(SmtpConfig):
    """Not in testing mode: no development code is ever shown."""

    TESTING = False
    SECRET_KEY = "production-like-secret"


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
def fake_smtp(monkeypatch):
    FakeSMTP.sent, FakeSMTP.logins, FakeSMTP.fail_login = [], [], False
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(email_service.smtplib, "SMTP_SSL", FakeSMTP)


def _register(client, email="ana@example.com", password="clave-segura-1"):
    client.get("/registro")
    client.post(
        "/registro",
        data={
            "csrf_token": csrf_from_page(client),
            "nombre": "Ana",
            "email": email,
            "password": password,
            "confirmacion": password,
        },
    )


def _code_from_last_email():
    body = FakeSMTP.sent[-1].get_body(("plain",)).get_content()
    return re.search(r"\b(\d{6})\b", body).group(1)


def _submit_code(client, code, password="otra-clave-2", confirmation=None):
    return client.post(
        "/verificar-codigo",
        data={
            "csrf_token": csrf_from_page(client),
            "codigo": code,
            "password": password,
            "confirmacion": confirmation or password,
        },
    )


def _login(client, password, email="ana@example.com"):
    return client.post(
        "/login",
        data={"csrf_token": csrf_from_page(client), "email": email, "password": password},
    )


def _request_code(client, email="ana@example.com"):
    return client.post(
        "/recuperar-contrasena", data={"csrf_token": csrf_from_page(client), "email": email}
    )


def test_recovery_sends_a_code_that_resets_the_password():
    client = test_client(create_app(SmtpConfig))
    _register(client)
    client.post("/logout", data={"csrf_token": csrf_from_page(client)})

    response = _request_code(client, "ANA@example.com")

    assert response.status_code == 303
    assert response.headers["Location"] == "/verificar-codigo"
    page = client.get("/verificar-codigo").text
    assert "te enviamos un código de 6 dígitos" in page
    assert "ana@example.com" in page
    assert "Modo desarrollo" not in page
    message = FakeSMTP.sent[0]
    assert message["To"] == "ana@example.com"
    assert message["From"] == "Nivora <nivora@example.com>"
    assert FakeSMTP.logins == [("nivora@example.com", "abcdefghijklmnop")]
    code = _code_from_last_email()
    assert message["Subject"] == f"{code} es tu código de Nivora"
    assert "15 minutos" in message.get_body(("plain",)).get_content()

    done = _submit_code(client, code)
    assert done.status_code == 200
    assert "Contraseña actualizada" in done.text
    assert _login(client, "otra-clave-2").headers["Location"] == "/aprender"

    # The code works only once.
    client.post("/logout", data={"csrf_token": csrf_from_page(client)})
    assert client.get("/verificar-codigo").headers["Location"] == "/recuperar-contrasena"


def test_wrong_code_explains_the_problem_and_locks_after_five_attempts():
    client = test_client(create_app(SmtpConfig))
    _register(client)
    _request_code(client)
    code = _code_from_last_email()
    wrong = "000000" if code != "000000" else "111111"

    first = _submit_code(client, wrong)
    assert first.status_code == 400
    assert "El código no es correcto" in first.text
    for _ in range(4):
        last = _submit_code(client, wrong)
    assert "superó los intentos" in last.text
    # Even the right code no longer works: a new one must be requested.
    assert "superó los intentos" in _submit_code(client, code).text
    assert _login(client, "otra-clave-2").headers["Location"] == "/login"


def test_code_form_validates_format_and_passwords():
    client = test_client(create_app(SmtpConfig))
    _register(client)
    _request_code(client)
    code = _code_from_last_email()

    assert "Escribe los 6 dígitos" in _submit_code(client, "12ab").text
    assert "al menos 8 caracteres" in _submit_code(client, code, "corta").text.lower()
    mismatch = _submit_code(client, code, "otra-clave-2", "otra-clave-3")
    assert "Las contraseñas no coinciden" in mismatch.text
    # Validation errors do not spend the code.
    assert "Contraseña actualizada" in _submit_code(client, f"{code[:3]} {code[3:]}").text


def test_a_new_code_replaces_the_previous_one_and_resending_is_throttled():
    client = test_client(create_app(SmtpConfig))
    _register(client)
    _request_code(client)
    first_code = _code_from_last_email()

    again = _request_code(client)
    assert again.headers["Location"] == "/verificar-codigo"
    assert "espera un minuto" in client.get("/verificar-codigo").text
    assert len(FakeSMTP.sent) == 1

    with client.session_transaction() as session:
        session["reset_code_sent_at"] = 0
    _request_code(client)
    assert len(FakeSMTP.sent) == 2
    second_code = _code_from_last_email()
    if second_code != first_code:  # 1 in a million they are equal
        assert "no es correcto" in _submit_code(client, first_code).text
    assert "Contraseña actualizada" in _submit_code(client, second_code).text


def test_unknown_email_gets_the_same_answer_without_sending_anything():
    client = test_client(create_app(SmtpConfig))

    response = _request_code(client, "nadie@example.com")

    assert response.headers["Location"] == "/verificar-codigo"
    assert "te enviamos un código" in client.get("/verificar-codigo").text
    assert FakeSMTP.sent == []
    assert "venció" in _submit_code(client, "123456").text


def test_smtp_failure_is_reported_honestly():
    client = test_client(create_app(ProductionLikeConfig))
    _register(client)
    FakeSMTP.fail_login = True

    response = _request_code(client)

    assert response.status_code == 503
    assert "No pudimos enviar el correo" in response.text
    assert "te enviamos" not in response.text


def test_missing_smtp_settings_are_reported_honestly():
    class NoSmtp(ProductionLikeConfig):
        SMTP_HOST = None

    client = test_client(create_app(NoSmtp))
    _register(client)
    response = _request_code(client)

    assert response.status_code == 503
    assert "no está configurado" in response.text
    assert FakeSMTP.sent == []


def test_development_mode_shows_a_test_code_when_email_is_not_configured():
    class DevNoSmtp(SmtpConfig):
        SMTP_HOST = None

    client = test_client(create_app(DevNoSmtp))
    _register(client)
    _request_code(client)
    page = client.get("/verificar-codigo").text

    assert "no está configurado" in page
    code = re.search(r"Tu código de prueba es <strong>(\d{6})</strong>", page).group(1)
    assert "Contraseña actualizada" in _submit_code(client, code).text


def test_invalid_email_is_rejected_inline():
    client = test_client(create_app(SmtpConfig))

    response = _request_code(client, "no-es-correo")

    assert response.status_code == 400
    assert "Introduce un correo electrónico válido" in response.text


def test_change_password_from_settings_sends_a_code_to_the_account_owner():
    client = test_client(create_app(SmtpConfig))
    _register(client)

    response = client.post("/ajustes/cambiar-contrasena", data={"csrf_token": csrf_from_page(client)})
    assert response.headers["Location"] == "/verificar-codigo"
    page = client.get("/verificar-codigo").text
    assert "Te enviamos un código de 6 dígitos a ana@example.com" in page
    body = FakeSMTP.sent[-1].get_body(("plain",)).get_content()
    assert "Hola Ana" in body and "cambiar tu contraseña" in body

    done = _submit_code(client, _code_from_last_email())
    assert "Volver a ajustes" in done.text


def test_change_password_without_smtp_explains_the_problem():
    class NoSmtp(ProductionLikeConfig):
        SMTP_HOST = None

    client = test_client(create_app(NoSmtp))
    _register(client)
    client.post("/ajustes/cambiar-contrasena", data={"csrf_token": csrf_from_page(client)})
    settings = client.get("/ajustes").text

    assert "no está configurado" in settings
    assert "Te enviamos un código" not in settings
    assert FakeSMTP.sent == []


def test_change_password_requires_login():
    client = test_client()
    response = client.post("/ajustes/cambiar-contrasena", data={"csrf_token": csrf_from_page(client)})
    assert response.headers["Location"] == "/login"


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


def test_registration_and_reset_share_the_same_live_password_rules():
    client = test_client(create_app(SmtpConfig))
    signup = client.get("/registro").text
    _register(client)
    _request_code(client)
    reset = client.get("/verificar-codigo").text

    for page in (signup, reset):
        assert "data-password-form" in page
        assert "/static/js/password.js" in page
        for rule in ("Al menos 8 caracteres", "Al menos una letra", "Al menos un número"):
            assert rule in page


# Equivalence classes and boundary values of the password rule (shared by
# registration and reset): exactly 7 vs 8 characters, missing letters or digits.
@pytest.mark.parametrize(
    "password, accepted",
    [
        ("abc1234", False),     # 7 characters: just below the limit
        ("abcd1234", True),     # 8 characters: on the limit
        ("abcdefgh", False),    # only letters
        ("12345678", False),    # only digits
        ("ñandú2024", True),    # non-ASCII letters count as letters
        ("", False),            # empty
    ],
)
def test_reset_applies_the_same_password_rule_as_registration(password, accepted):
    client = test_client(create_app(SmtpConfig))
    _register(client)
    _request_code(client)

    response = _submit_code(client, _code_from_last_email(), password)

    if accepted:
        assert "Contraseña actualizada" in response.text
    else:
        assert response.status_code == 400
        assert "al menos 8 caracteres" in response.text.lower()
