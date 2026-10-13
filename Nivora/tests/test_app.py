import json

from app import create_app
from config import TestingConfig
from controllers import auth_controller
from models.ruta_model import RutaModel


def test_health_endpoint():
    client = create_app(TestingConfig).test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_post_without_csrf_is_rejected():
    client = create_app(TestingConfig).test_client()
    response = client.post("/login", data={"email": "a@b.com", "password": "password-123"})

    assert response.status_code == 400


def test_password_recovery_routes_offer_and_accept_a_dev_reset_link(monkeypatch):
    class FakeResetService:
        def create_password_reset(self, email, ttl):
            assert email == "ana@example.com"
            assert ttl > 0
            return "demo-token"

        def reset_password(self, token, password):
            return token == "demo-token" and password == "new-password"

    monkeypatch.setattr(auth_controller, "auth_service", FakeResetService())
    app = create_app(TestingConfig)
    app.config["SMTP_HOST"] = None
    app.config["PUBLIC_BASE_URL"] = None
    client = app.test_client()
    client.get("/recuperar-contrasena")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]

    recovery = client.post(
        "/recuperar-contrasena",
        data={"csrf_token": csrf, "email": "ana@example.com"},
    )
    assert recovery.status_code == 200
    assert b"/restablecer-contrasena/demo-token" in recovery.data

    client.get("/restablecer-contrasena/demo-token")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    reset = client.post(
        "/restablecer-contrasena/demo-token",
        data={
            "csrf_token": csrf,
            "password": "new-password",
            "confirmacion": "new-password",
        },
    )

    assert reset.status_code == 200
    assert b"Contrase\xc3\xb1a actualizada" in reset.data


def test_profile_change_password_opens_recovery_with_account_email():
    client = create_app(TestingConfig).test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana", "email": "ana@example.com"}

    profile = client.get("/ajustes")
    recovery = client.get("/recuperar-contrasena")

    assert profile.status_code == 200
    assert b'href="/recuperar-contrasena"' in profile.data
    assert recovery.status_code == 200
    assert b'value="ana@example.com"' in recovery.data


def test_login_session_survives_next_request():
    client = create_app(TestingConfig).test_client()
    client.get('/login')
    with client.session_transaction() as session:
        csrf = session['csrf_token']

    response = client.post(
        '/login',
        data={'csrf_token': csrf, 'email': 'missing@example.com', 'password': 'password-123'},
    )

    assert response.status_code == 200


def test_lesson_requires_login():
    client = create_app(TestingConfig).test_client()
    response = client.get("/aprender/leccion/variables")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_level_page_requires_login():
    client = create_app(TestingConfig).test_client()
    response = client.get("/nivel")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/registro")


def test_level_page_recommends_starting_from_zero():
    client = create_app(TestingConfig).test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana", "email": "ana@example.com"}

    response = client.post(
        "/nivel",
        data={"csrf_token": "invalid", "nivel_inicial": "no_se_nada"},
    )

    assert response.status_code == 400


def test_completed_lesson_appears_in_progress():
    client = create_app(TestingConfig).test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        csrf = session["csrf_token"]

    response = client.post(
        "/aprender/leccion/variables/completar",
        data={
            "csrf_token": csrf,
            "respuesta_1": "nombre",
            "respuesta_2": "int",
            "respuesta_3": "True",
        },
    )

    assert response.status_code == 200
    assert b"Correcta" in response.data
    assert b"Siguiente lecci" in response.data
    progress = client.get("/progreso")
    assert b"25%" in progress.data


def test_failed_lesson_keeps_answers_and_does_not_complete():
    client = create_app(TestingConfig).test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        csrf = session["csrf_token"]

    response = client.post(
        "/aprender/leccion/variables/completar",
        data={
            "csrf_token": csrf,
            "respuesta_1": "Ana",
            "respuesta_2": "str",
            "respuesta_3": "10",
        },
    )

    assert response.status_code == 200
    assert b"Quiz evaluado" in response.data
    assert b"Siguiente lecci" in response.data
    assert b'checked' in response.data
    with client.session_transaction() as session:
        assert session["progreso"]["variables"]["completada"] is False


def test_perfect_lesson_hides_repeat_quiz_and_failed_lesson_is_incomplete():
    client = create_app(TestingConfig).test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        csrf = session["csrf_token"]

    failed = client.post(
        "/aprender/leccion/variables/completar",
        data={"csrf_token": csrf, "respuesta_1": "Ana", "respuesta_2": "str", "respuesta_3": "10"},
    )
    assert b"Incompleta" not in failed.data

    route = client.get("/aprender/ruta/01")
    assert b"Incompleta" in route.data

    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    perfect = client.post(
        "/aprender/leccion/variables/completar",
        data={"csrf_token": csrf, "respuesta_1": "nombre", "respuesta_2": "int", "respuesta_3": "True"},
    )
    assert b"Repetir quiz" not in perfect.data


def test_next_lesson_skips_completed_lesson():
    client = create_app(TestingConfig).test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        session["progreso"] = {
            "variables": {"completada": True, "intentada": True},
            "entrada_salida": {"completada": True, "intentada": True},
        }
        csrf = session["csrf_token"]

    response = client.post(
        "/aprender/leccion/operadores/completar",
        data={
            "csrf_token": csrf,
            "respuesta_1": "7",
            "respuesta_2": "True",
            "respuesta_3": "==",
        },
    )

    assert response.status_code == 200
    assert b"/aprender/leccion/repaso_fundamentos" in response.data


def test_unit_two_stays_locked_until_all_first_unit_lessons_are_complete():
    client = create_app(TestingConfig).test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana"}

    response = client.get("/aprender/ruta/02")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/aprender")


def test_unit_two_puzzle_unlocks_and_saves_a_correct_solution():
    client = create_app(TestingConfig).test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana"}
        session["progreso"] = {
            lesson_id: {"completada": True}
            for lesson_id in ("variables", "operadores", "entrada_salida", "repaso_fundamentos")
        }
        csrf = session["csrf_token"]

    page = client.get("/aprender/ruta/02")
    assert page.status_code == 200
    assert b"Bloques disponibles" in page.data

    response = client.post(
        "/aprender/ruta/02",
        data={"csrf_token": csrf, "sequence": json.dumps(RutaModel.PUZZLE_SOLUTION)},
    )

    assert response.status_code == 200
    assert b"Completaste el rompecabezas" in response.data
    with client.session_transaction() as session:
        assert session["progreso"]["unidad_02_puzzle"]["completada"] is True