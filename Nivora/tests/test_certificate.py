"""Course completion certificate (point 5)."""

import re

import pytest

from models.ruta_model import RutaModel
from repositories.certificate_repository import CertificateRepository
from repositories.progress_repository import ProgressRepository
from tests.conftest import csrf_from_page
from tests.test_app import test_client


def _register(client, email="ana@example.com"):
    client.get("/registro")
    client.post(
        "/registro",
        data={
            "csrf_token": csrf_from_page(client),
            "nombre": "Ana Pérez",
            "email": email,
            "password": "clave-segura-1",
            "confirmacion": "clave-segura-1",
        },
    )
    with client.session_transaction() as session:
        return session["usuario"]["id_persona"]


def _complete(user_id, how_many):
    lessons = RutaModel.obtener_lecciones()[:how_many]
    for lesson in lessons:
        ProgressRepository().save_activity(
            user_id, lesson["id"], {"completada": True, "intentada": True, "puntuacion": 3, "total": 3}
        )


# Boundary values on the number of completed lessons (16 in total).
@pytest.mark.parametrize("completed, available", [(0, False), (15, False), (16, True)])
def test_certificate_requires_every_lesson(completed, available):
    client = test_client()
    user_id = _register(client)
    _complete(user_id, completed)

    response = client.get("/certificado")

    if available:
        assert response.status_code == 200
        assert "Certificado de finalización" in response.text
        assert "Ana Pérez" in response.text
    else:
        assert response.status_code == 403
        assert f"Llevas {completed}" in response.text
        assert "Código de verificación" not in response.text


def test_certificate_requires_login():
    response = test_client().get("/certificado")
    assert response.headers["Location"] == "/login"


def test_attempted_but_failed_lessons_do_not_count():
    client = test_client()
    user_id = _register(client)
    _complete(user_id, 15)
    ProgressRepository().save_activity(
        user_id, "proyecto_final", {"completada": False, "intentada": True, "puntuacion": 2, "total": 3}
    )

    assert client.get("/certificado").status_code == 403


def test_completion_is_read_from_the_database_not_from_the_session():
    client = test_client()
    _register(client)
    with client.session_transaction() as session:
        session["progreso"] = {
            lesson["id"]: {"completada": True} for lesson in RutaModel.obtener_lecciones()
        }

    assert client.get("/certificado").status_code == 403


def test_certificate_is_issued_once_with_a_stable_date_and_code():
    client = test_client()
    user_id = _register(client)
    _complete(user_id, 16)

    first = client.get("/certificado").text
    second = client.get("/certificado").text
    code = re.search(r"NIV-[A-Z0-9]{4}-[A-Z0-9]{4}", first).group(0)

    assert code in second
    assert CertificateRepository().find_by_user(user_id)["codigo"] == code


def test_certificate_code_can_be_verified_publicly():
    client = test_client()
    user_id = _register(client)
    _complete(user_id, 16)
    code = re.search(r"NIV-[A-Z0-9]{4}-[A-Z0-9]{4}", client.get("/certificado").text).group(0)

    anonymous = test_client()
    valid = anonymous.get(f"/certificado/verificar/{code.lower()}")
    invalid = anonymous.get("/certificado/verificar/NIV-XXXX-XXXX")

    assert valid.status_code == 200
    assert "Certificado válido" in valid.text and "Ana Pérez" in valid.text
    assert invalid.status_code == 404
    assert "No encontramos" in invalid.text


def test_progress_page_and_last_lesson_lead_to_the_certificate():
    client = test_client()
    user_id = _register(client)
    _complete(user_id, 15)
    with client.session_transaction() as session:
        session["progreso"] = ProgressRepository().find_by_user(user_id)

    assert "Te faltan 1" in client.get("/progreso").text
    client.post(
        "/aprender/leccion/proyecto_final/completar",
        data={
            "csrf_token": csrf_from_page(client),
            "respuesta_1": "Aprobado",
            "respuesta_2": "par",
            "respuesta_3": "reutilizar",
        },
    )
    lesson = client.get("/aprender/leccion/proyecto_final").text
    assert "Obtener mi certificado" in lesson
    assert "Ver mi certificado" in client.get("/progreso").text
    assert client.get("/certificado").status_code == 200
