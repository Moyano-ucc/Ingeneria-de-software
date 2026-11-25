"""Shared helpers for the test suite (no tests here)."""

import base64
import json
import re
from contextlib import contextmanager

from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner

from app import create_app
from config import TestingConfig
from models.ruta_model import RutaModel
from repositories.progress_repository import ProgressRepository


class SessionTestClient(TestClient):
    """TestClient that can read and edit the signed session cookie."""

    @contextmanager
    def session_transaction(self):
        cookie = self.cookies.get("nivora_session", domain="testserver.local", path="/")
        if cookie:
            serialized = TimestampSigner("test-secret-key").unsign(cookie)
            session = json.loads(base64.b64decode(serialized))
        else:
            session = {}
        yield session
        encoded = base64.b64encode(json.dumps(session).encode("utf-8"))
        signed = TimestampSigner("test-secret-key").sign(encoded).decode("utf-8")
        self.cookies.clear()
        self.cookies.set("nivora_session", signed, domain="testserver.local", path="/")


def test_client(app=None):
    """A client that does not follow redirects, so each Location can be checked."""
    return SessionTestClient(app or create_app(TestingConfig), follow_redirects=False)


test_client.__test__ = False


def csrf_from_page(client):
    """Read the CSRF token from a rendered form (works with any Host header)."""
    html = client.get("/recuperar-contrasena").text
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def register_user(
    client, email="ana@example.com", password="clave-segura-1", nombre="Ana", return_id=True
):
    """Create an account through the real form and return its id_persona.

    Use ``return_id=False`` with apps whose session key is not the test key.
    """
    client.get("/registro")
    client.post(
        "/registro",
        data={
            "csrf_token": csrf_from_page(client),
            "nombre": nombre,
            "email": email,
            "password": password,
            "confirmacion": password,
        },
    )
    if not return_id:
        return None
    with client.session_transaction() as session:
        return session["usuario"]["id_persona"]


def login(client, email="ana@example.com", password="clave-segura-1"):
    return client.post(
        "/login",
        data={"csrf_token": csrf_from_page(client), "email": email, "password": password},
    )


def complete_lessons(user_id, how_many):
    """Mark the first ``how_many`` lessons as completed in the database."""
    for lesson in RutaModel.obtener_lecciones()[:how_many]:
        ProgressRepository().save_activity(
            user_id,
            lesson["id"],
            {"completada": True, "intentada": True, "puntuacion": 3, "total": 3},
        )


def logged_in_client(progreso=None, usuario=None):
    """A client with a session user (no database account) and optional progress."""
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = usuario or {"id_persona": 1, "nombre": "Ana"}
        if progreso is not None:
            session["progreso"] = progreso
    return client


UNIT_LESSONS = {
    1: ("variables", "operadores", "entrada_salida", "repaso_fundamentos"),
    2: ("condicionales", "while", "for", "control_rompecabezas"),
    3: ("listas", "estructuras", "recorrido", "proyecto_estructuras"),
    4: ("funciones", "parametros", "alcance", "proyecto_final"),
}


def completed(*units):
    """Session progress with every lesson of the given units completed."""
    return {
        lesson_id: {"completada": True}
        for unit in units
        for lesson_id in UNIT_LESSONS[unit]
    }
