#pip install -r requirements.txt
import os
import secrets

from flask import Flask, render_template, request
from controllers.aprender_controller import aprender_bp
from controllers.auth_controller import auth_bp
from controllers.practica_controller import practica_bp
from controllers.progreso_controller import progreso_bp
from config import Config
from errors.handlers import register_error_handlers
from security import csrf_token, validate_csrf


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    if not app.config.get("TESTING"):
        app.config["SECRET_KEY"] = secrets.token_urlsafe(32)
        app.config["SESSION_COOKIE_NAME"] = f"nivora_session_{secrets.token_urlsafe(12)}"
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def protect_state_changing_requests():
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            validate_csrf(request.form.get("csrf_token"))

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    app.register_blueprint(aprender_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(practica_bp)
    app.register_blueprint(progreso_bp)
    register_error_handlers(app)

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.get('/health')
    def health():
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=int(os.environ.get("PORT", "5000")))