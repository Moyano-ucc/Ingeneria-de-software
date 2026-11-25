"""Smoke tests: a quick check (seconds) that the main pages are alive. Run with: pytest -m smoke"""

import pytest

from tests.helpers import csrf_from_page, logged_in_client, register_user, test_client


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


@pytest.mark.parametrize(
    "path", ["/", "/login", "/registro", "/recuperar-contrasena", "/api/health", "/api/lecciones", "/docs"]
)
def test_public_pages_respond(path):
    assert test_client().get(path).status_code == 200


@pytest.mark.parametrize(
    "path",
    ["/aprender", "/aprender/ruta/01", "/aprender/leccion/variables", "/practica", "/progreso", "/ajustes"],
)
def test_main_pages_respond_for_a_logged_in_student(path):
    assert logged_in_client(progreso={}).get(path).status_code == 200


def test_a_student_can_register_answer_a_quiz_and_see_progress():
    client = test_client()
    register_user(client)
    client.post(
        "/aprender/leccion/variables/completar",
        data={"csrf_token": csrf_from_page(client), "respuesta_1": "nombre", "respuesta_2": "int", "respuesta_3": "True"},
    )
    assert "1 de 16 lecciones" in client.get("/progreso").text
