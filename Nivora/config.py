import os


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


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SESSION_COOKIE_SECURE = False
