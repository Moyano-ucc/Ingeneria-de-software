"""Quiz answers persistence, quiz repetition and lesson review (E02, M02, M05)."""

import re

import pytest

from database.database import DatabaseConnection
from tests.test_app import test_client


CORRECT = {"respuesta_1": "nombre", "respuesta_2": "int", "respuesta_3": "True"}
WRONG = {"respuesta_1": "Ana", "respuesta_2": "str", "respuesta_3": "10"}


@pytest.fixture(autouse=True)
def isolate_database(tmp_path, monkeypatch):
    monkeypatch.setenv("NIVORA_DATABASE_PATH", str(tmp_path / "nivora.db"))


def _csrf(client):
    html = client.get("/recuperar-contrasena").text
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def _register_and_login(client, email="ana@example.com"):
    client.get("/registro")
    client.post(
        "/registro",
        data={
            "csrf_token": _csrf(client),
            "nombre": "Ana",
            "email": email,
            "password": "clave-segura-1",
            "confirmacion": "clave-segura-1",
        },
    )
    client.post("/nivel", data={"csrf_token": _csrf(client), "nivel_inicial": "no_se_nada"})


def _submit(client, lesson_id, answers):
    return client.post(
        f"/aprender/leccion/{lesson_id}/completar",
        data={"csrf_token": _csrf(client), **answers},
    )


def _progress_rows():
    connection = DatabaseConnection().connect()
    try:
        return [
            dict(row)
            for row in connection.execute(
                "SELECT leccion_id, completada, intentos, respuestas FROM PROGRESO_LECCION"
            ).fetchall()
        ]
    finally:
        connection.close()


def test_answers_survive_going_to_the_practice_challenge_and_back():
    client = test_client()
    _register_and_login(client)

    _submit(client, "variables", WRONG)
    assert client.get("/practica?ejercicio=variables").status_code == 200
    lesson = client.get("/aprender/leccion/variables").text

    assert "Quiz evaluado" in lesson
    assert lesson.count("checked") == 3
    assert 'value="Ana" required checked' in lesson
    assert "Resultado: 0/3" in lesson


def test_answers_survive_a_new_session_because_they_are_stored_in_the_database():
    client = test_client()
    _register_and_login(client)
    _submit(client, "variables", WRONG)
    client.post("/logout", data={"csrf_token": _csrf(client)})

    client.get("/login")
    client.post(
        "/login",
        data={"csrf_token": _csrf(client), "email": "ana@example.com", "password": "clave-segura-1"},
    )
    lesson = client.get("/aprender/leccion/variables").text

    assert "Quiz evaluado" in lesson
    assert lesson.count("checked") == 3


def test_repeat_button_sits_right_below_the_evaluated_message():
    client = test_client()
    _register_and_login(client)
    _submit(client, "variables", WRONG)
    lesson = client.get("/aprender/leccion/variables").text

    message = lesson.index("Pulsa “Repetir quiz” para intentarlo de nuevo.")
    button = lesson.index(">Repetir quiz</a>")
    challenge = lesson.index("Reto práctico")
    assert message < button < challenge
    assert lesson.count(">Repetir quiz</a>") == 1


def test_repeat_quiz_starts_a_clean_attempt_and_keeps_a_single_progress_row():
    client = test_client()
    _register_and_login(client)
    _submit(client, "variables", WRONG)

    fresh = client.get("/aprender/leccion/variables?repetir=1").text
    assert "Evaluar quiz" in fresh
    assert "checked" not in fresh
    assert "Quiz evaluado" not in fresh

    _submit(client, "variables", CORRECT)
    rows = _progress_rows()
    assert len(rows) == 1
    assert rows[0]["intentos"] == 2
    assert rows[0]["completada"] == 1
    assert "lección completada" in client.get("/aprender/leccion/variables").text


def test_reviewing_a_completed_lesson_never_resets_progress():
    client = test_client()
    _register_and_login(client)
    _submit(client, "variables", CORRECT)

    route = client.get("/aprender/ruta/01").text
    assert "/aprender/leccion/variables?repetir=1" in route
    assert ">Repasar</a>" in route

    _submit(client, "variables", WRONG)
    rows = _progress_rows()
    assert len(rows) == 1
    assert rows[0]["completada"] == 1
    assert rows[0]["intentos"] == 2
    with client.session_transaction() as session:
        assert session["progreso"]["variables"]["completada"] is True

    # The next lesson stays unlocked and overall progress is unchanged.
    assert client.get("/aprender/leccion/operadores").status_code == 200
    assert "25%" in client.get("/progreso").text
    retry = client.get("/aprender/leccion/variables").text
    assert "Volver a la unidad" in retry
