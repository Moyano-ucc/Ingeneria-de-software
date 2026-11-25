"""Unit tests of the practice evaluation service: code analysis, puzzles and blocks."""

import json

import pytest

from models.ejercicios_practica import EJERCICIOS
from services.practica_service import evaluate_code, puzzle_feedback, validate_puzzle_answer


EXERCISES = {exercise["id"]: exercise for exercise in EJERCICIOS}


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
