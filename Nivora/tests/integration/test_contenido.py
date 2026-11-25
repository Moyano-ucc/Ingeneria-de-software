"""Integration tests of the course content: lessons in the database, theory and exercises."""

import builtins
import contextlib
import io

import pytest

from models.contenido_lecciones import LESSON_MATERIAL
from models.ejercicios_practica import EJERCICIOS
from models.ruta_model import RutaModel
from tests.helpers import test_client


def _run(code, inputs=()):
    values = iter(inputs)
    output = io.StringIO()

    def fake_input(prompt=""):
        value = next(values)
        print(prompt + value, file=output)
        return value

    with contextlib.redirect_stdout(output):
        exec(code, {"input": fake_input, "__builtins__": builtins})
    return output.getvalue().rstrip("\n")


def test_every_lesson_has_complete_theory():
    lesson_ids = {lesson["id"] for lesson in RutaModel.obtener_lecciones()}
    assert set(LESSON_MATERIAL) == lesson_ids
    for material in LESSON_MATERIAL.values():
        for key in ("explicacion", "analogia", "ejemplo", "lineas", "salida", "errores", "reto"):
            assert material[key], key


@pytest.mark.parametrize("lesson_id", sorted(LESSON_MATERIAL))
def test_theory_examples_print_what_the_lesson_says(lesson_id):
    material = LESSON_MATERIAL[lesson_id]
    assert _run(material["ejemplo"], material.get("entrada", [])) == material["salida"]
    assert _run(material["reto"]["codigo"]) == material["reto"]["respuesta"]


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
