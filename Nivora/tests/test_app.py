from app import create_app
from config import TestingConfig


def test_health_endpoint():
    client = create_app(TestingConfig).test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_post_without_csrf_is_rejected():
    client = create_app(TestingConfig).test_client()
    response = client.post("/login", data={"email": "a@b.com", "password": "password-123"})

    assert response.status_code == 400


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