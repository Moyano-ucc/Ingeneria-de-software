import logging
import os
import secrets

import uvicorn
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from api_routes import api_router
from config import Config
from controllers.aprender_controller import aprender_router
from controllers.auth_controller import auth_router
from controllers.certificado_controller import certificado_router
from controllers.practica_controller import practica_router
from controllers.progreso_controller import progreso_router
from errors.handlers import register_error_handlers


def create_app(config_object=Config) -> FastAPI:
    testing = bool(getattr(config_object, "TESTING", False))
    secret_key = getattr(config_object, "SECRET_KEY", "dev-only-change-me")
    if not testing and secret_key == "dev-only-change-me":
        secret_key = secrets.token_urlsafe(32)

    app = FastAPI(
        title="Nivora",
        description="Plataforma para aprender Python con rutas, prácticas y progreso.",
        version="1.0.0",
        debug=bool(getattr(config_object, "DEBUG", False)),
    )
    app.state.settings = config_object
    app.state.testing = testing
    app.state.session_cookie = "nivora_session"
    app.state.max_content_length = getattr(config_object, "MAX_CONTENT_LENGTH", 1_048_576)
    app.state.logger = logging.getLogger("nivora")
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        session_cookie="nivora_session",
        max_age=getattr(config_object, "SESSION_COOKIE_MAX_AGE", 15 * 60),
        same_site=getattr(config_object, "SESSION_COOKIE_SAMESITE", "lax"),
        https_only=bool(getattr(config_object, "SESSION_COOKIE_SECURE", False)),
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        if response.headers.get("content-type", "").startswith("text/html"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"
        return response

    @app.get("/", name="home")
    async def home(request: Request):
        from views.responses import render_template

        return render_template(request, "index.html")

    @app.get("/health", name="health")
    async def health():
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(aprender_router)
    app.include_router(practica_router)
    app.include_router(progreso_router)
    app.include_router(certificado_router)
    app.include_router(api_router)
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
        name="static",
    )
    register_error_handlers(app)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=os.environ.get("NIVORA_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("NIVORA_DEBUG") == "1",
    )
