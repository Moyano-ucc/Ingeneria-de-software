"""Unit tests of the SMTP e-mail service configuration."""

from config import TestingConfig
from services.email_service import EmailService


class SmtpConfig(TestingConfig):
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USERNAME = "nivora@example.com"
    SMTP_PASSWORD = "abcd efgh ijkl mnop"
    SMTP_FROM = None
    SMTP_USE_TLS = True
    SMTP_USE_SSL = False
    PASSWORD_RESET_TOKEN_TTL = 900


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
