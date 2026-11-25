"""System tests of the practice page: code editor, blocks, puzzles and guidance."""

import json
import re

from models.ejercicios_practica import EJERCICIOS
from tests.helpers import test_client


EXERCISES = {exercise["id"]: exercise for exercise in EJERCICIOS}


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
