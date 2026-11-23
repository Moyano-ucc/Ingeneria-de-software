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
    SESSION_PERMANENT = False
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024
    SMTP_HOST = os.environ.get("NIVORA_SMTP_HOST")
    SMTP_PORT = int(os.environ.get("NIVORA_SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("NIVORA_SMTP_USERNAME")
    SMTP_PASSWORD = os.environ.get("NIVORA_SMTP_PASSWORD")
    SMTP_FROM = os.environ.get("NIVORA_SMTP_FROM", "Nivora <noreply@localhost>")
    SMTP_USE_TLS = os.environ.get("NIVORA_SMTP_USE_TLS", "1") == "1"
    PASSWORD_RESET_TOKEN_TTL = int(os.environ.get("NIVORA_PASSWORD_RESET_TTL", "3600"))
    PUBLIC_BASE_URL = os.environ.get("NIVORA_PUBLIC_URL")


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SESSION_COOKIE_SECURE = False
