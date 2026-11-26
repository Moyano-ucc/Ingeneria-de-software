"""System tests of the «Mis apuntes» REST API: every HTTP method, path and
query parameters, status codes, validation and ownership."""

import pytest

from app import create_app
from config import TestingConfig
from controllers.apuntes_api_controller import obtener_repositorio
from tests.helpers import register_user, test_client


def _student(email="ana@example.com"):
    client = test_client()
    register_user(client, email=email)
    return client


def _create(client, leccion="variables", contenido="Una variable guarda un dato", destacado=False):
    return client.post(
        "/api/apuntes", json={"leccion": leccion, "contenido": contenido, "destacado": destacado}
    )


def test_full_crud_cycle_uses_every_http_method():
    client = _student()

    created = _create(client)                                   # POST
    assert created.status_code == 201
    note = created.json()
    assert created.headers["Location"] == f"/api/apuntes/{note['id']}"
    assert note["leccion"] == "variables" and note["destacado"] is False

    assert client.get(f"/api/apuntes/{note['id']}").json() == note   # GET (path param)

    replaced = client.put(                                      # PUT: replaces everything
        f"/api/apuntes/{note['id']}",
        json={"leccion": "operadores", "contenido": "== compara", "destacado": True},
    )
    assert replaced.status_code == 200
    assert replaced.json()["leccion"] == "operadores"
    assert replaced.json()["destacado"] is True

    patched = client.patch(f"/api/apuntes/{note['id']}", json={"destacado": False})  # PATCH
    assert patched.status_code == 200
    assert patched.json()["contenido"] == "== compara"          # untouched field kept
    assert patched.json()["destacado"] is False
    assert patched.json()["actualizado"] >= replaced.json()["actualizado"]

    deleted = client.delete(f"/api/apuntes/{note['id']}")      # DELETE
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/api/apuntes/{note['id']}").status_code == 404


def test_list_filters_by_lesson_with_a_query_parameter_and_puts_starred_first():
    client = _student()
    _create(client, "variables", "primero")
    _create(client, "variables", "importante", destacado=True)
    _create(client, "operadores", "otra lección")

    all_notes = client.get("/api/apuntes").json()
    variables = client.get("/api/apuntes", params={"leccion": "variables"}).json()

    assert len(all_notes) == 3
    assert [n["contenido"] for n in variables] == ["importante", "primero"]


@pytest.mark.parametrize(
    "method, path",
    [
        ("get", "/api/apuntes"),
        ("post", "/api/apuntes"),
        ("get", "/api/apuntes/1"),
        ("put", "/api/apuntes/1"),
        ("patch", "/api/apuntes/1"),
        ("delete", "/api/apuntes/1"),
    ],
)
def test_every_endpoint_requires_a_session(method, path):
    kwargs = {"json": {"leccion": "variables", "contenido": "x"}} if method in ("post", "put", "patch") else {}
    response = getattr(test_client(), method)(path, **kwargs)

    assert response.status_code == 401
    assert response.json() == {"detail": "Inicia sesión para usar tus apuntes"}


def test_a_student_cannot_see_or_change_another_students_notes():
    ana = _student("ana@example.com")
    note_id = _create(ana).json()["id"]
    luis = _student("luis@example.com")

    assert luis.get(f"/api/apuntes/{note_id}").status_code == 404
    assert luis.put(f"/api/apuntes/{note_id}", json={"leccion": "variables", "contenido": "x"}).status_code == 404
    assert luis.patch(f"/api/apuntes/{note_id}", json={"contenido": "x"}).status_code == 404
    assert luis.delete(f"/api/apuntes/{note_id}").status_code == 404
    assert luis.get("/api/apuntes").json() == []
    assert ana.get(f"/api/apuntes/{note_id}").json()["contenido"] == "Una variable guarda un dato"


# Boundary values of the note length (1 to 2000 characters after trimming).
@pytest.mark.parametrize(
    "contenido, status",
    [("", 422), ("   ", 422), ("a", 201), ("a" * 2000, 201), ("a" * 2001, 422)],
)
def test_content_length_boundaries(contenido, status):
    assert _create(_student(), contenido=contenido).status_code == status


@pytest.mark.parametrize(
    "body",
    [
        {},                                   # PATCH without fields
        {"contenido": None},                  # null is not a valid value
        {"leccion": "no-existe"},             # unknown lesson
        {"destacado": "quizás"},              # wrong type
    ],
)
def test_invalid_patch_bodies_are_rejected(body):
    client = _student()
    note_id = _create(client).json()["id"]

    assert client.patch(f"/api/apuntes/{note_id}", json=body).status_code == 422


def test_path_parameter_must_be_a_positive_integer_and_lesson_must_exist():
    client = _student()

    assert client.get("/api/apuntes/abc").status_code == 422
    assert client.get("/api/apuntes/0").status_code == 422
    assert _create(client, leccion="no-existe").status_code == 422


def test_put_requires_the_complete_resource():
    client = _student()
    note_id = _create(client).json()["id"]

    assert client.put(f"/api/apuntes/{note_id}", json={"contenido": "sin lección"}).status_code == 422


def test_endpoints_are_documented_in_swagger():
    paths = test_client().get("/openapi.json").json()["paths"]

    assert set(paths["/api/apuntes"]) == {"get", "post"}
    assert set(paths["/api/apuntes/{apunte_id}"]) == {"get", "put", "patch", "delete"}


class InMemoryNotes:
    """Fake repository: the controller depends on the dependency, not on SQLite."""

    def __init__(self):
        self.notes = {}

    def list(self, user_id, leccion=None):
        return [n for n in self.notes.values() if leccion in (None, n["leccion"])]

    def create(self, user_id, leccion, contenido, destacado=False):
        note = {"id": len(self.notes) + 1, "leccion": leccion, "contenido": contenido,
                "destacado": destacado, "creado": 1.0, "actualizado": 1.0}
        self.notes[note["id"]] = note
        return note


def test_the_repository_can_be_replaced_through_dependency_injection():
    app = create_app(TestingConfig)
    fake = InMemoryNotes()
    app.dependency_overrides[obtener_repositorio] = lambda: fake
    client = test_client(app)
    with client.session_transaction() as session:
        session["usuario"] = {"id_persona": 99, "nombre": "Ana"}

    client.post("/api/apuntes", json={"leccion": "variables", "contenido": "en memoria"})

    assert client.get("/api/apuntes").json()[0]["contenido"] == "en memoria"
    assert fake.notes[1]["contenido"] == "en memoria"
