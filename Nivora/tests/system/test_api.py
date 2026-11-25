"""System tests of the REST API (the same requests can be run from Postman)."""

import pytest

from tests.helpers import test_client


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


def test_lesson_list_contains_the_sixteen_lessons():
    lessons = test_client().get("/api/lecciones").json()["lecciones"]

    assert len(lessons) == 16
    assert {"id", "titulo", "unidad", "descripcion"} <= set(lessons[0])


# Boundary values of the "answers" list: the model accepts 1 to 3 items and
# every lesson has exactly 3 questions.
@pytest.mark.parametrize(
    "answers, status",
    [
        ([], 422),                                  # below the minimum
        (["nombre"], 400),                          # minimum accepted by the model, incomplete
        (["nombre", "int"], 400),                   # incomplete
        (["nombre", "int", "True"], 200),           # exact
        (["nombre", "int", "True", "extra"], 422),  # above the maximum
    ],
)
def test_evaluation_answer_count_boundaries(answers, status):
    response = test_client().post("/api/lecciones/variables/evaluar", json={"answers": answers})
    assert response.status_code == status


# Equivalence classes of the score: all correct, some correct, none correct.
@pytest.mark.parametrize(
    "answers, score, completed",
    [
        (["nombre", "int", "True"], 3, True),
        (["nombre", "int", "False"], 2, False),
        (["Ana", "str", "10"], 0, False),
    ],
)
def test_evaluation_score_classes(answers, score, completed):
    result = test_client().post("/api/lecciones/variables/evaluar", json={"answers": answers}).json()
    assert (result["puntuacion"], result["completada"]) == (score, completed)


def test_api_errors_are_json_and_unknown_lessons_return_404():
    client = test_client()

    missing = client.post("/api/lecciones/no-existe/evaluar", json={"answers": ["a", "b", "c"]})
    malformed = client.post("/api/lecciones/variables/evaluar", json={"respuestas": []})

    assert missing.status_code == 404
    assert missing.json() == {"detail": "Lección no encontrada"}
    assert malformed.status_code == 422
