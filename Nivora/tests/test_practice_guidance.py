"""Lesson theory, guided practice feedback and easy-level blocks (M01, M03, M04)."""

import builtins
import contextlib
import io
import json
import re

import pytest

from models.contenido_lecciones import LESSON_MATERIAL
from models.ejercicios_practica import EJERCICIOS
from models.ruta_model import RutaModel
from services.practica_service import evaluate_code, puzzle_feedback, validate_puzzle_answer
from tests.test_app import test_client


EXERCISES = {exercise["id"]: exercise for exercise in EJERCICIOS}


@pytest.fixture(autouse=True)
def isolate_database(tmp_path, monkeypatch):
    monkeypatch.setenv("NIVORA_DATABASE_PATH", str(tmp_path / "nivora.db"))


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


# ---------------------------------------------------------------- theory

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


def test_lesson_page_shows_the_extended_theory():
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 1, "nombre": "Ana"}
    html = client.get("/aprender/leccion/variables").text

    for text in ("En la vida diaria", "¿Qué hace cada línea?", "Resultado en pantalla",
                 "Errores comunes", "¿qué imprime?", "<details"):
        assert text in html


# ---------------------------------------------------------------- code feedback

@pytest.mark.parametrize(
    "exercise_id, code",
    [
        ("variables", "edad=20"),
        ("variables", "edad = (20)"),
        ("operadores", "total = 4 + 3"),
        ("entrada_salida", "nombre = input('¿Cómo te llamas? ')"),
        ("repaso_fundamentos", "cantidad = 5\nprecio = 2\nprint(cantidad * precio)"),
    ],
)
def test_equivalent_solutions_are_accepted(exercise_id, code):
    assert evaluate_code(EXERCISES[exercise_id], code) == (True, [])


@pytest.mark.parametrize(
    "exercise_id, code, expected",
    [
        ("variables", "", "Todavía no escribiste código"),
        ("variables", 'edad = "20"', "entre comillas"),
        ("variables", "Edad = 20", "mayúsculas"),
        ("variables", "edad == 20", "un solo ="),
        ("variables", "20 = edad", "a la izquierda del ="),
        ("variables", "edad = 21", "no es el que pide"),
        ("operadores", "total = 7", "resultado a mano"),
        ("operadores", "total = 3 * 4", "sumar (+)"),
        ("entrada_salida", 'nombre = print("Tu nombre")', "input() recibe datos"),
        ("entrada_salida", 'nombre = input("Tu nombre"', "cerrar un paréntesis"),
        ("entrada_salida", 'nombre = input("Tu nombre)', "cerrar unas comillas"),
        ("repaso_fundamentos", "precio = 2\ncantidad = 5", "print()"),
        ("repaso_fundamentos", "precio = 2\ncantidad = 5\nprint(precio + cantidad)", "print()"),
    ],
)
def test_wrong_code_gets_an_explanation(exercise_id, code, expected):
    correct, feedback = evaluate_code(EXERCISES[exercise_id], code)
    assert correct is False
    assert any(expected in message for message in feedback), feedback
    # The feedback never reveals the full answer.
    assert all(EXERCISES[exercise_id]["respuesta"] not in message for message in feedback)


# ---------------------------------------------------------------- blocks

def test_only_easy_exercises_use_blocks_and_their_tokens_build_the_answer():
    for exercise in EJERCICIOS:
        if exercise["nivel"] != "Fácil":
            assert "bloques" not in exercise
            continue
        blocks = exercise["bloques"]
        for line in blocks["solucion"]:
            assert all(token in blocks["fichas"] for token in line)
        # Same joining rule as static/js/bloques.js.
        code = "\n".join(" ".join(line) for line in blocks["solucion"])
        assert evaluate_code(exercise, code) == (True, [])


def test_easy_practice_page_offers_blocks_without_leaking_the_solution():
    client = test_client()
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana"}

    easy = client.get("/practica?ejercicio=variables").text
    medium = client.get("/practica?ejercicio=condicionales").text

    assert "data-practice-blocks" in easy
    assert "/static/js/bloques.js" in easy
    assert 'id="codigo"' in easy
    fichas = json.loads(re.search(r"data-fichas='([^']+)'", easy).group(1))
    assert fichas == EXERCISES["variables"]["bloques"]["fichas"]
    assert '"solucion"' not in re.search(r"data-fichas='[^']+'", easy).group(0)
    assert "data-practice-blocks" not in medium


def test_code_built_with_blocks_is_evaluated_like_typed_code():
    client = test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana"}
        csrf = session["csrf_token"]

    response = client.post(
        "/practica",
        data={
            "csrf_token": csrf,
            "ejercicio": "repaso_fundamentos",
            "modo": "bloques",
            "codigo": "precio = 2\ncantidad = 5\nprint( precio * cantidad )",
        },
    )
    assert "¡Respuesta correcta!" in client.get(response.headers["Location"]).text


# ---------------------------------------------------------------- guided practice

def test_practice_shows_objective_steps_and_progressive_hints():
    client = test_client()
    client.get("/login")
    with client.session_transaction() as session:
        session["usuario"] = {"nombre": "Ana"}
        csrf = session["csrf_token"]

    page = client.get("/practica?ejercicio=variables").text
    assert "Objetivo:" in page
    assert page.count("<details class=\"practice-hint-more\"") == 2
    assert page.count("practice-hint-more\" open") == 0

    for attempt in range(2):
        response = client.post(
            "/practica",
            data={"csrf_token": csrf, "ejercicio": "variables", "codigo": 'edad = "20"'},
        )
        page = client.get(response.headers["Location"]).text
        assert "entre comillas" in page
    assert page.count("practice-hint-more\" open") == 2
    assert "Llevas 2 intentos" in page

    response = client.post(
        "/practica",
        data={"csrf_token": csrf, "ejercicio": "variables", "codigo": "edad = 20"},
    )
    assert "¡Respuesta correcta!" in client.get(response.headers["Location"]).text


def test_puzzle_feedback_explains_the_mistake_without_solving_it():
    ordenar = EXERCISES["condicionales"]
    answer, correct = validate_puzzle_answer(ordenar, json.dumps(["si", "menor", "sino", "adulto"]))
    assert correct is False
    feedback = puzzle_feedback(ordenar, answer)
    assert feedback[0] == "2 de 4 bloques están en su lugar."
    assert "línea 2" in feedback[1]
    assert "sangría" in feedback[2]

    completar = EXERCISES["while"]
    answer, _ = validate_puzzle_answer(completar, json.dumps({"limite": "uno"}))
    assert "el 1 no se muestra" in puzzle_feedback(completar, answer)[0]

    emparejar = EXERCISES["estructuras"]
    answer, _ = validate_puzzle_answer(
        emparejar, json.dumps({"lista": "inmutable", "tupla": "mutable", "diccionario": "clave_valor"})
    )
    assert puzzle_feedback(emparejar, answer)[0] == "Tienes 1 de 3 parejas correctas."
    assert puzzle_feedback(emparejar, {})[0] == "Te faltan 3 parejas por conectar."
