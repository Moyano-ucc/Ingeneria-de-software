import secrets

from flask import abort, session


def csrf_token():
    token = session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def validate_csrf(form_token):
    expected = session.get("csrf_token")
    if not expected or not form_token or not secrets.compare_digest(expected, form_token):
        abort(400, description="Token CSRF inválido")
