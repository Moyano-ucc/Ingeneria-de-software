import base64
from contextlib import contextmanager
import json

from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
import pytest

from app import create_app
from config import TestingConfig
from controllers import auth_controller
from controllers.practica_controller import EJERCICIOS
from models.ruta_model import RutaModel


class SessionTestClient(TestClient):
    @contextmanager
    def session_transaction(self):
        cookie = self.cookies.get(
            "nivora_session",
            domain="testserver.local",
            path="/",
        )
        if cookie:
            serialized = TimestampSigner("test-secret-key").unsign(cookie)
            session = json.loads(base64.b64decode(serialized))
        else:
            session = {}
        yield session
        encoded = base64.b64encode(json.dumps(session).encode("utf-8"))
        signed = TimestampSigner("test-secret-key").sign(encoded).decode("utf-8")
        self.cookies.clear()
        self.cookies.set(
            "nivora_session",
            signed,
            domain="testserver.local",
            path="/",
        )


def test_client(app=None):
    return SessionTestClient(app or create_app(TestingConfig), follow_redirects=False)


test_client.__test__ = False


@pytest.fixture(autouse=True)
def isolate_database(tmp_path, monkeypatch):
    monkeypatch.setenv("NIVORA_DATABASE_PATH", str(tmp_path / "nivora.db"))


def test_health_endpoint():
    client = test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_homepage_enables_animations_even_with_reduced_motion_preference():
    response = test_client().get("/")

    assert response.status_code == 200
    assert 'data-motion-toggle' not in response.text
    assert '/static/js/motion.js' in response.text


def test_fastapi_docs_and_lesson_evaluation_are_available():
    client = test_client()

    docs = client.get("/docs")
    evaluation = client.post(
        "/api/lecciones/variables/evaluar",
        json={"answers": ["nombre", "int", "True"]},
    )

    assert docs.status_code == 200
    assert evaluation.status_code == 200
    assert evaluation.json() == {
        "leccion": "variables",
        "puntuacion": 3,
        "total": 3,
        "completada": True,
    }


def test_api_lesson_endpoint_supports_path_parameter():
    client = test_client()

    lesson = client.get("/api/lecciones/variables")
    missing = client.get("/api/lecciones/no-existe")

    assert lesson.status_code == 200
    assert lesson.json()["id"] == "variables"
    assert missing.status_code == 404


def test_practice_page_accepts_a_solution():
    client = test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana", "email": "ana@example.com"}
        csrf = session["csrf_token"]

    response = client.post(
        "/practica",
        data={
            "csrf_token": csrf,
            "ejercicio": "variables",
            "codigo": "edad = 20",
        },
    )

    assert response.status_code == 303
    result = client.get(response.headers["Location"])
    assert result.status_code == 200
    assert "¡Respuesta correcta!" in result.text


def test_first_unit_keeps_code_editor_and_later_units_use_different_puzzles():
    client = test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana"}

    first_unit = [
        client.get(f"/practica?ejercicio={lesson_id}")
        for lesson_id in ("variables", "operadores", "entrada_salida", "repaso_fundamentos")
    ]
    assert all(b'id="codigo"' in response.content for response in first_unit)
    assert all(b"data-practice-puzzle" not in response.content for response in first_unit)

    later_unit = {
        exercise["id"]: exercise["tipo"]
        for exercise in EJERCICIOS
        if "tipo" in exercise
    }
    assert set(later_unit.values()) == {"ordenar", "completar", "emparejar"}
    for lesson_id, puzzle_type in later_unit.items():
        response = client.get(f"/practica?ejercicio={lesson_id}")
        assert response.status_code == 200
        assert f'data-kind="{puzzle_type}"'.encode() in response.content
        assert b'id="codigo"' not in response.content


def test_interactive_practice_puzzles_accept_valid_solutions_and_reject_unknown_blocks():
    client = test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana"}
        csrf = session["csrf_token"]

    for exercise in EJERCICIOS:
        if "tipo" not in exercise:
            continue
        response = client.post(
            "/practica",
            data={
                "csrf_token": csrf,
                "ejercicio": exercise["id"],
                "respuesta": json.dumps(exercise["rompecabezas"]["solucion"]),
            },
        )
        assert response.status_code == 303
        result = client.get(response.headers["Location"])
        assert "¡Reto completado!" in result.text

    invalid = client.post(
        "/practica",
        data={
            "csrf_token": csrf,
            "ejercicio": "condicionales",
            "respuesta": json.dumps(["si", "adulto", "sino", "menor", "desconocido"]),
        },
    )
    result = client.get(invalid.headers["Location"])
    assert "Aún no está listo" in result.text


def test_every_lesson_has_unique_questions_and_a_guided_code_exercise():
    lessons = RutaModel.obtener_lecciones()

    assert len(lessons) == 16
    for lesson in lessons:
        assert len(lesson["questions"]) == 3
        assert len({question for question, _options in lesson["questions"]}) == 3
        assert all(len(options) == 4 for _question, options in lesson["questions"])
        assert all(
            answer in {value for value, _label in options}
            for answer, (_question, options) in zip(
                lesson["answers"],
                lesson["questions"],
            )
        )
    assert {lesson["id"] for lesson in lessons} == {
        exercise["id"] for exercise in EJERCICIOS
    }

    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        session["progreso"] = {}

    lesson_page = client.get("/aprender/leccion/variables")
    practice = client.get("/practica?ejercicio=variables")

    assert b"Reto pr" in lesson_page.content
    assert lesson_page.text.count('type="radio"') == 12
    assert b"/practica?ejercicio=variables" in lesson_page.content
    assert b"Tu c" in practice.content


def test_existing_quiz_rows_are_refreshed_with_the_new_answer_options():
    RutaModel.obtener_lecciones()
    connection = RutaModel.database.connect()
    try:
        connection.execute(
            "UPDATE EJERCICIO_LECCION SET opciones = ? WHERE id_leccion = 1 AND numero = 1",
            (json.dumps([{"value": "nombre", "label": "nombre"}]),),
        )
        connection.commit()
    finally:
        connection.close()

    refreshed_lessons = RutaModel.obtener_lecciones()
    variables = next(lesson for lesson in refreshed_lessons if lesson["id"] == "variables")

    assert len(variables["questions"][0][1]) == 4
    assert "nombre" in {value for value, _label in variables["questions"][0][1]}


def test_app_keeps_stable_session_cookie_name_and_configured_secret():
    from app import create_app
    from config import Config

    class ProductionConfig(Config):
        TESTING = False
        SECRET_KEY = "secreto-estable"

    app = create_app(ProductionConfig)

    assert app.state.settings.SECRET_KEY == "secreto-estable"
    assert app.state.session_cookie == "nivora_session"


def test_session_cookie_expires_after_fifteen_minutes():
    response = test_client().get("/login")

    assert "max-age=900" in response.headers["set-cookie"].lower()


def test_post_without_csrf_is_rejected():
    client = test_client()
    response = client.post("/login", data={"email": "a@b.com", "password": "password-123"})

    assert response.status_code == 400


def test_password_recovery_routes_offer_and_accept_a_dev_reset_link(monkeypatch):
    class FakeResetService:
        def create_password_reset(self, email, ttl):
            assert email == "ana@example.com"
            assert ttl > 0
            return "demo-token"

        def reset_password(self, token, password):
            return token == "demo-token" and password == "new-password-123"

        @staticmethod
        def password_is_strong(password):
            return (
                len(password) >= 8
                and any(character.isalpha() for character in password)
                and any(character.isdigit() for character in password)
            )

    monkeypatch.setattr(auth_controller, "auth_service", FakeResetService())
    class RecoveryTestingConfig(TestingConfig):
        SMTP_HOST = None
        PUBLIC_BASE_URL = "http://127.0.0.1:8000"

    app = create_app(RecoveryTestingConfig)
    client = test_client(app)
    client.get("/recuperar-contrasena")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]

    recovery = client.post(
        "/recuperar-contrasena",
        data={"csrf_token": csrf, "email": "ana@example.com"},
    )
    assert recovery.status_code == 200
    assert (
        b"http://127.0.0.1:8000/restablecer-contrasena/demo-token"
        in recovery.content
    )

    client.get("/restablecer-contrasena/demo-token")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    reset = client.post(
        "/restablecer-contrasena/demo-token",
        data={
            "csrf_token": csrf,
            "password": "new-password-123",
            "confirmacion": "new-password-123",
        },
    )

    assert reset.status_code == 200
    assert "Contraseña actualizada" in reset.text


def test_profile_change_password_opens_recovery_with_account_email():
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana", "email": "ana@example.com"}

    profile = client.get("/ajustes")
    recovery = client.get("/recuperar-contrasena")

    assert profile.status_code == 200
    assert b'href="/recuperar-contrasena"' in profile.content
    assert recovery.status_code == 200
    assert b'value="ana@example.com"' in recovery.content


def test_login_session_survives_next_request():
    client = test_client()
    client.get('/login')
    with client.session_transaction() as session:
        csrf = session['csrf_token']

    response = client.post(
        '/login',
        data={'csrf_token': csrf, 'email': 'missing@example.com', 'password': 'password-123'},
    )

    assert response.status_code == 303
    login_page = client.get(response.headers["Location"])
    assert b"Correo o contrase\xc3\xb1a incorrectos" in login_page.content
    assert b'value="password-123"' not in login_page.content
    assert b'id="email-error"' in login_page.content
    assert b'id="password-error"' in login_page.content
    assert b'class="form-message"' not in login_page.content


def test_auth_forms_disable_caching_and_authenticated_user_does_not_return_to_signup():
    client = test_client()
    registration = client.get("/registro")

    assert registration.headers["Cache-Control"] == "no-store, max-age=0"
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana", "recomendacion": {"codigo": "inicial"}}

    response = client.get("/registro")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/aprender")


def test_registration_checks_confirmation_and_password_strength_inline():
    client = test_client()
    client.get("/registro")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]

    response = client.post(
        "/registro",
        data={
            "csrf_token": csrf,
            "nombre": "Ana",
            "email": "ana@example.com",
            "password": "solo-letras",
            "confirmacion": "solo-letras",
        },
    )

    assert response.status_code == 303
    form = client.get(response.headers["Location"])
    assert b"Usa al menos 8 caracteres, con letras y n" in form.content
    assert b"class=\"form-message\"" not in form.content
    assert b"value=\"solo-letras\"" not in form.content


def test_registration_confirmation_mismatch_is_shown_by_the_password_fields():
    client = test_client()
    client.get("/registro")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]

    response = client.post(
        "/registro",
        data={
            "csrf_token": csrf,
            "nombre": "Ana",
            "email": "ana@example.com",
            "password": "clave1234",
            "confirmacion": "clave5678",
        },
    )
    form = client.get(response.headers["Location"])

    assert response.status_code == 303
    assert form.content.count(b"Las contrase") == 2
    assert b"clave1234" not in form.content
    assert b"clave5678" not in form.content


def test_registration_login_and_back_navigation_keep_user_in_the_flow():
    client = test_client()
    client.get("/registro")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]

    registration = client.post(
        "/registro",
        data={
            "csrf_token": csrf,
            "nombre": "Ana",
            "email": "ana@example.com",
            "password": "clave1234",
            "confirmacion": "clave1234",
        },
    )
    assert registration.status_code == 303
    assert registration.headers["Location"].endswith("/nivel")
    assert client.get("/registro").headers["Location"].endswith("/nivel")

    client.get("/nivel")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    client.post("/logout", data={"csrf_token": csrf})

    client.get("/login")
    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    login = client.post(
        "/login",
        data={
            "csrf_token": csrf,
            "email": "ana@example.com",
            "password": "clave1234",
        },
    )

    assert login.status_code == 303
    assert login.headers["Location"].endswith("/aprender")
    assert client.get("/login").headers["Location"].endswith("/aprender")


def test_lesson_requires_login():
    client = test_client()
    response = client.get("/aprender/leccion/variables")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_level_page_requires_login():
    client = test_client()
    response = client.get("/nivel")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/registro")


def test_level_page_recommends_starting_from_zero():
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana", "email": "ana@example.com"}

    response = client.post(
        "/nivel",
        data={"csrf_token": "invalid", "nivel_inicial": "no_se_nada"},
    )

    assert response.status_code == 400


def test_completed_lesson_appears_in_progress():
    client = test_client()
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

    assert response.status_code == 303
    result = client.get(response.headers["Location"])
    assert b"Correcta" in result.content
    assert b"Siguiente lecci" in result.content
    progress = client.get("/progreso")
    assert b"25%" in progress.content


def test_failed_lesson_keeps_answers_and_does_not_complete():
    client = test_client()
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

    assert response.status_code == 303
    result = client.get(response.headers["Location"])
    assert b"Quiz evaluado" in result.content
    assert b"Repetir quiz" in result.content
    assert b'checked' in result.content
    with client.session_transaction() as session:
        assert session["progreso"]["variables"]["completada"] is False


def test_perfect_lesson_hides_repeat_quiz_and_failed_lesson_is_incomplete():
    client = test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        csrf = session["csrf_token"]

    failed = client.post(
        "/aprender/leccion/variables/completar",
        data={"csrf_token": csrf, "respuesta_1": "Ana", "respuesta_2": "str", "respuesta_3": "10"},
    )
    assert failed.status_code == 303

    route = client.get("/aprender/ruta/01")
    assert b"Incompleta" in route.content

    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    perfect = client.post(
        "/aprender/leccion/variables/completar",
        data={"csrf_token": csrf, "respuesta_1": "nombre", "respuesta_2": "int", "respuesta_3": "True"},
    )
    result = client.get(perfect.headers["Location"])
    assert b"Repetir quiz" not in result.content


def test_next_lesson_skips_completed_lesson():
    client = test_client()
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

    assert response.status_code == 303
    result = client.get(response.headers["Location"])
    assert b"/aprender/leccion/repaso_fundamentos" in result.content


def test_unit_two_stays_locked_until_all_first_unit_lessons_are_complete():
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana"}

    response = client.get("/aprender/ruta/02")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/aprender")


def test_unit_two_puzzle_unlocks_and_saves_a_correct_solution():
    client = test_client()
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
    assert b"Bloques disponibles" in page.content

    partial = client.post(
        "/aprender/ruta/02",
        data={
            "csrf_token": csrf,
            "sequence": json.dumps(["number", "positive"]),
        },
    )
    partial_page = client.get(partial.headers["Location"])
    assert partial.status_code == 303
    assert b'["number", "positive"]' in partial_page.content

    with client.session_transaction() as session:
        csrf = session["csrf_token"]
    response = client.post(
        "/aprender/ruta/02",
        data={"csrf_token": csrf, "sequence": json.dumps(RutaModel.PUZZLE_SOLUTION)},
    )

    assert response.status_code == 303
    result = client.get(response.headers["Location"])
    assert b"Completaste el rompecabezas" in result.content
    with client.session_transaction() as session:
        assert session["progreso"]["unidad_02_puzzle"]["completada"] is True


def test_unit_two_route_shows_its_lessons_and_locks_unit_three():
    client = test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        session["progreso"] = {
            lesson_id: {"completada": True}
            for lesson_id in (
                "variables",
                "operadores",
                "entrada_salida",
                "repaso_fundamentos",
            )
        }

    unit_two = client.get("/aprender/ruta/02")
    locked_lesson = client.get("/aprender/leccion/listas")

    assert unit_two.status_code == 200
    assert b"Condicionales" in unit_two.content
    assert b"Ciclos while" in unit_two.content
    assert b"Bloques disponibles" in unit_two.content
    assert locked_lesson.status_code == 302
    assert locked_lesson.headers["Location"].endswith("/aprender")


def test_completing_unit_two_unlocks_unit_three():
    client = test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        session["progreso"] = {
            lesson_id: {"completada": True}
            for lesson_id in (
                "variables",
                "operadores",
                "entrada_salida",
                "repaso_fundamentos",
                "condicionales",
                "while",
                "for",
                "control_rompecabezas",
            )
        }
        csrf = session["csrf_token"]

    puzzle = client.post(
        "/aprender/ruta/02",
        data={
            "csrf_token": csrf,
            "sequence": json.dumps(RutaModel.PUZZLE_SOLUTION),
        },
    )
    puzzle_page = client.get(puzzle.headers["Location"])
    unit_three = client.get("/aprender/ruta/03")

    assert puzzle.status_code == 303
    assert b"Continuar a unidad 03" in puzzle_page.content
    assert unit_three.status_code == 200
    assert b"Listas" in unit_three.content


def test_failed_lesson_does_not_unlock_the_next_lesson():
    client = test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        csrf = session["csrf_token"]

    client.post(
        "/aprender/leccion/variables/completar",
        data={
            "csrf_token": csrf,
            "respuesta_1": "incorrecta",
            "respuesta_2": "str",
            "respuesta_3": "10",
        },
    )
    next_lesson = client.get("/aprender/leccion/operadores")

    assert next_lesson.status_code == 302
    assert next_lesson.headers["Location"].endswith("/aprender/ruta/01")


def test_logout_clears_the_user_session():
    client = test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana"}
        csrf = session["csrf_token"]

    response = client.post("/logout", data={"csrf_token": csrf})

    assert response.status_code == 303
    assert response.headers["Location"].endswith("/")
    with client.session_transaction() as session:
        assert "usuario" not in session