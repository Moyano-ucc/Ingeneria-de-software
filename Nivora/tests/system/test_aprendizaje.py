"""System tests of units, lessons, quizzes, review and progress through HTTP."""

import pytest

from database.database import DatabaseConnection
from tests.helpers import completed, csrf_from_page, logged_in_client, register_user, test_client


CORRECT = {"respuesta_1": "nombre", "respuesta_2": "int", "respuesta_3": "True"}


WRONG = {"respuesta_1": "Ana", "respuesta_2": "str", "respuesta_3": "10"}


_register_and_login = register_user


def _submit(client, lesson_id, answers):
    return client.post(
        f"/aprender/leccion/{lesson_id}/completar",
        data={"csrf_token": csrf_from_page(client), **answers},
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


def test_lesson_requires_login():
    client = test_client()
    response = client.get("/aprender/leccion/variables")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


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


def test_unit_two_stays_locked_until_all_first_unit_lessons_are_complete():
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana"}

    response = client.get("/aprender/ruta/02")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/aprender")


def test_unit_two_uses_the_common_unit_page_without_an_extra_final_challenge():
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        session["progreso"] = {lesson_id: {"completada": True} for lesson_id in ("variables", "operadores", "entrada_salida", "repaso_fundamentos")}

    unit_two = client.get("/aprender/ruta/02")
    locked_lesson = client.get("/aprender/leccion/listas")

    assert unit_two.status_code == 200
    assert "Condicionales" in unit_two.text and "Ciclos while" in unit_two.text
    assert "Reto final" not in unit_two.text
    assert "Bloques disponibles" not in unit_two.text
    assert "Continuar a la unidad 03" not in unit_two.text
    assert locked_lesson.status_code == 302
    assert locked_lesson.headers["Location"].endswith("/aprender")
    # The route no longer accepts the old puzzle submission.
    assert client.post("/aprender/ruta/02").status_code == 405


def test_unit_two_lessons_can_be_reviewed_once_completed():
    """Regression: unit 2 had its own template without the «Repasar» button."""
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        session["progreso"] = {
            lesson_id: {"completada": True} for lesson_id in ("variables", "operadores", "entrada_salida", "repaso_fundamentos") + ("condicionales", "while", "for", "control_rompecabezas")
        }

    unit_two = client.get("/aprender/ruta/02").text

    for lesson_id in ("condicionales", "while", "for", "control_rompecabezas"):
        assert f"/aprender/leccion/{lesson_id}?repetir=1" in unit_two
    assert unit_two.count(">Repasar</a>") == 4
    review = client.get("/aprender/leccion/condicionales?repetir=1")
    assert review.status_code == 200
    assert "Evaluar quiz" in review.text


def test_completing_unit_two_lessons_unlocks_unit_three():
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        session["progreso"] = {
            lesson_id: {"completada": True} for lesson_id in ("variables", "operadores", "entrada_salida", "repaso_fundamentos") + ("condicionales", "while", "for", "control_rompecabezas")
        }

    unit_two = client.get("/aprender/ruta/02")
    unit_three = client.get("/aprender/ruta/03")

    assert "Continuar a la unidad 03" in unit_two.text
    assert unit_three.status_code == 200
    assert "Listas" in unit_three.text


def test_old_unit_two_puzzle_progress_is_kept_but_ignored():
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
        session["progreso"] = {
            **{lesson_id: {"completada": True} for lesson_id in ("variables", "operadores", "entrada_salida", "repaso_fundamentos")},
            "unidad_02_puzzle": {"completada": True},
        }

    progress = client.get("/progreso").text

    assert "4/16" in progress or "25%" in progress
    assert client.get("/aprender/ruta/03").status_code == 302


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
    client.post("/logout", data={"csrf_token": csrf_from_page(client)})

    client.get("/login")
    client.post(
        "/login",
        data={"csrf_token": csrf_from_page(client), "email": "ana@example.com", "password": "clave-segura-1"},
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


def test_lesson_page_shows_the_extended_theory():
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
    html = client.get("/aprender/leccion/variables").text

    for text in ("En la vida diaria", "¿Qué hace cada línea?", "Resultado en pantalla",
                 "Errores comunes", "¿qué imprime?", "<details"):
        assert text in html


# Decision table: access to a lesson.
#   session | unit unlocked | previous lesson completed | result
#   no      | -             | -                         | /login
#   yes     | no            | -                         | /aprender
#   yes     | yes           | no                        | unit page
#   yes     | yes           | yes / first lesson        | 200
@pytest.mark.parametrize(
    "session, progreso, lesson, expected",
    [
        (False, {}, "variables", "/login"),
        (True, {}, "condicionales", "/aprender"),
        (True, {}, "operadores", "/aprender/ruta/01"),
        (True, {}, "variables", 200),
        (True, {"variables": {"completada": True}}, "operadores", 200),
        (True, completed(1), "condicionales", 200),
        (True, completed(1), "while", "/aprender/ruta/02"),
    ],
)
def test_lesson_access_decision_table(session, progreso, lesson, expected):
    client = logged_in_client(progreso=progreso) if session else test_client()

    response = client.get(f"/aprender/leccion/{lesson}")

    if expected == 200:
        assert response.status_code == 200
    else:
        assert response.headers["Location"] == expected


# Decision table: unit unlocking, one unit at a time.
@pytest.mark.parametrize(
    "progreso, unlocked",
    [
        ({}, ["01"]),
        (completed(1), ["01", "02"]),
        (completed(1, 2), ["01", "02", "03"]),
        (completed(1, 2, 3), ["01", "02", "03", "04"]),
        (completed(2, 3), ["01"]),  # later units do not count without the first
    ],
)
def test_unit_unlocking_decision_table(progreso, unlocked):
    client = logged_in_client(progreso=progreso)

    for unit in ("01", "02", "03", "04"):
        status = client.get(f"/aprender/ruta/{unit}").status_code
        assert (status == 200) is (unit in unlocked), unit


# Boundary values of the quiz score: 2/3 does not complete, 3/3 does.
@pytest.mark.parametrize(
    "answers, completada",
    [
        ({"respuesta_1": "nombre", "respuesta_2": "int", "respuesta_3": "10"}, False),
        ({"respuesta_1": "nombre", "respuesta_2": "int", "respuesta_3": "True"}, True),
    ],
)
def test_quiz_completion_boundary(answers, completada):
    client = logged_in_client(progreso={})
    client.post(
        "/aprender/leccion/variables/completar",
        data={"csrf_token": csrf_from_page(client), **answers},
    )
    with client.session_transaction() as session:
        assert session["progreso"]["variables"]["completada"] is completada
