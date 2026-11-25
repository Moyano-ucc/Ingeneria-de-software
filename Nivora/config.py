import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).with_name(".env"), override=False)


class Config:
    SECRET_KEY = os.environ.get("NIVORA_SECRET_KEY", "dev-only-change-me")
    DATABASE_PATH = os.environ.get("NIVORA_DATABASE_PATH")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("NIVORA_COOKIE_SECURE", "0") == "1"
    SESSION_COOKIE_MAX_AGE = 15 * 60
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024
    SMTP_HOST = os.environ.get("NIVORA_SMTP_HOST")
    SMTP_PORT = int(os.environ.get("NIVORA_SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("NIVORA_SMTP_USERNAME")
    SMTP_PASSWORD = os.environ.get("NIVORA_SMTP_PASSWORD")
    SMTP_FROM = os.environ.get("NIVORA_SMTP_FROM")
    SMTP_USE_TLS = os.environ.get("NIVORA_SMTP_USE_TLS", "1") == "1"
    SMTP_USE_SSL = os.environ.get("NIVORA_SMTP_USE_SSL", "0") == "1"
    # Validity of the 6-digit password reset code, in seconds (15 minutes).
    PASSWORD_RESET_TOKEN_TTL = int(os.environ.get("NIVORA_PASSWORD_RESET_TTL", "900"))
    # Seconds a student must wait before asking for another code.
    PASSWORD_RESET_RESEND_SECONDS = 60


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SESSION_COOKIE_SECURE = False
    # Tests never use the real mail server, even if NIVORA_SMTP_* exist in the
    # environment (for example, as Codespaces secrets).
    SMTP_HOST = None
    SMTP_USERNAME = None
    SMTP_PASSWORD = None
    SMTP_FROM = None
