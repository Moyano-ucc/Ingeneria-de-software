"""Integration tests: repositories and services against a real SQLite file."""

import json

import pytest

from werkzeug.security import check_password_hash, generate_password_hash

from database.database import DatabaseConnection
from models.ruta_model import RutaModel
from repositories.certificate_repository import CertificateRepository
from repositories.progress_repository import ProgressRepository
from repositories.user_repository import UserRepository
from services.auth_service import AuthService


def test_reset_code_is_single_use_and_persists_in_fresh_sqlite(tmp_path):
    database = DatabaseConnection(config={"database_path": str(tmp_path / "nivora.db")})
    users = UserRepository(database)
    users.create("Ana", "ana@example.com", generate_password_hash("old-password"))
    service = AuthService(users)

    code, user = service.create_reset_code("ANA@example.com", ttl=60)

    assert len(code) == 6 and code.isdigit()
    assert user["correo"] == "ana@example.com"
    assert service.reset_password_with_code("ana@example.com", code, "new-password-123") == "ok"
    assert check_password_hash(
        users.find_by_email("ana@example.com")["contrasena"],
        "new-password-123",
    )
    assert service.reset_password_with_code("ana@example.com", code, "another-password-1") == "expired"


def test_reset_code_expires_and_locks_after_too_many_attempts(tmp_path):
    database = DatabaseConnection(config={"database_path": str(tmp_path / "nivora.db")})
    users = UserRepository(database)
    users.create("Ana", "ana@example.com", generate_password_hash("old-password"))
    service = AuthService(users)

    expired_code, _ = service.create_reset_code("ana@example.com", ttl=-1)
    assert service.reset_password_with_code("ana@example.com", expired_code, "new-password-1") == "expired"

    code, _ = service.create_reset_code("ana@example.com", ttl=60)
    wrong = "000000" if code != "000000" else "111111"
    results = [
        service.reset_password_with_code("ana@example.com", wrong, "new-password-1")
        for _ in range(AuthService.RESET_CODE_MAX_ATTEMPTS)
    ]
    assert results[:-1] == ["invalid"] * (AuthService.RESET_CODE_MAX_ATTEMPTS - 1)
    assert results[-1] == "expired"
    assert service.reset_password_with_code("ana@example.com", code, "new-password-1") == "expired"


def test_database_creates_a_custom_parent_directory(tmp_path):
    database_path = tmp_path / "azure-data" / "nivora.db"
    database = DatabaseConnection(config={"database_path": str(database_path)})

    connection = database.connect()
    connection.close()

    assert database_path.exists()


def test_existing_quiz_rows_are_refreshed_with_the_new_answer_options():
    RutaModel.obtener_lecciones()
    connection = RutaModel.database.connect()
    try:
        connection.execute(
            "UPDATE EJERCICIO_LECCION SET opciones = ? WHERE id_leccion = 1 AND numero = 1",
            (json.dumps([{"value": "nombre", "label": "nombre"}]),),
        )
        connection.commit()
    finally:
        connection.close()

    # Content is refreshed when the application starts again.
    DatabaseConnection.initialized_paths.clear()
    RutaModel.clear_cache()
    refreshed_lessons = RutaModel.obtener_lecciones()
    variables = next(lesson for lesson in refreshed_lessons if lesson["id"] == "variables")

    assert len(variables["questions"][0][1]) == 4
    assert "nombre" in {value for value, _label in variables["questions"][0][1]}


def _users_with_ana():
    users = UserRepository()
    users.create("Ana", "ana@example.com", generate_password_hash("old-password-1"))
    return users, users.find_by_email("ana@example.com")["id_persona"]


# Boundary values of the code expiry: one instant before, exactly at, and after.
@pytest.mark.parametrize("offset, expected", [(-0.001, "ok"), (0, "expired"), (1, "expired")])
def test_reset_code_expiry_boundary(offset, expected):
    users, user_id = _users_with_ana()
    users.create_password_reset(user_id, "hash-del-codigo", 1_000.0)

    result = users.consume_reset_code(
        user_id, "hash-del-codigo", generate_password_hash("new-password-1"), 1_000.0 + offset, 5
    )

    assert result == expected


# Boundary values of the attempt limit (5): the 4th wrong attempt still allows
# a retry, the 5th locks the code.
@pytest.mark.parametrize("wrong_attempts, expected_last", [(4, "invalid"), (5, "expired")])
def test_reset_code_attempt_limit_boundary(wrong_attempts, expected_last):
    users, user_id = _users_with_ana()
    users.create_password_reset(user_id, "hash-correcto", 9e12)

    results = [
        users.consume_reset_code(user_id, "hash-incorrecto", "x", 1.0, 5)
        for _ in range(wrong_attempts)
    ]

    assert results[-1] == expected_last


def test_progress_upsert_keeps_one_row_counts_attempts_and_never_uncompletes():
    repository = ProgressRepository()
    repository.save_activity(1, "variables", {"completada": True, "intentada": True, "puntuacion": 3, "total": 3}, ["a"])
    repository.save_activity(1, "variables", {"completada": False, "intentada": True, "puntuacion": 1, "total": 3}, ["b"])

    connection = DatabaseConnection().connect()
    try:
        rows = connection.execute(
            "SELECT completada, puntuacion, intentos FROM PROGRESO_LECCION WHERE id_persona = 1"
        ).fetchall()
    finally:
        connection.close()

    assert [tuple(row) for row in rows] == [(1, 3, 2)]
    assert repository.find_last_answers(1, "variables") == ["b"]


def test_certificate_is_issued_once_per_student():
    users, user_id = _users_with_ana()
    repository = CertificateRepository()

    first = repository.issue(user_id)
    second = repository.issue(user_id)

    assert first == second
    assert repository.find_by_code(first["codigo"].lower())["nombre"] == "Ana"
    assert repository.find_by_code("NIV-0000-0000") is None


def test_legacy_plain_text_password_is_accepted_once_and_rehashed():
    users = UserRepository()
    users.create("Ana", "ana@example.com", "texto-plano-1")

    assert AuthService(users).authenticate("ana@example.com", "texto-plano-1")["nombre"] == "Ana"
    stored = users.find_by_email("ana@example.com")["contrasena"]
    assert stored != "texto-plano-1"
    assert check_password_hash(stored, "texto-plano-1")


def test_schema_migration_keeps_existing_progress_rows(tmp_path):
    """A database created before the new columns keeps its data after connecting."""
    import sqlite3

    path = tmp_path / "legacy.db"
    legacy = sqlite3.connect(path)
    legacy.executescript(
        """
        CREATE TABLE PROGRESO_LECCION (
            id_persona INTEGER NOT NULL, leccion_id TEXT NOT NULL,
            completada INTEGER NOT NULL DEFAULT 0, intentada INTEGER NOT NULL DEFAULT 0,
            puntuacion INTEGER NOT NULL DEFAULT 0, total INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (id_persona, leccion_id));
        CREATE TABLE PASSWORD_RESET (
            token_hash TEXT PRIMARY KEY, id_persona INTEGER NOT NULL,
            expires_at REAL NOT NULL, used_at REAL);
        INSERT INTO PROGRESO_LECCION VALUES (7, 'variables', 1, 1, 3, 3);
        """
    )
    legacy.commit()
    legacy.close()

    connection = DatabaseConnection(config={"database_path": str(path)}).connect()
    try:
        row = connection.execute(
            "SELECT completada, intentos, respuestas FROM PROGRESO_LECCION WHERE id_persona = 7"
        ).fetchone()
        reset_columns = {r["name"] for r in connection.execute("PRAGMA table_info(PASSWORD_RESET)")}
    finally:
        connection.close()

    assert tuple(row) == (1, 0, None)
    assert "intentos" in reset_columns


def test_concurrent_first_connections_do_not_collide(tmp_path):
    """Regression (found with the load test): simultaneous first requests ran the
    migration twice and failed with «duplicate column name»."""
    import threading

    path = str(tmp_path / "concurrente.db")
    errors = []

    def connect():
        try:
            DatabaseConnection(config={"database_path": path}).connect().close()
        except Exception as error:  # noqa: BLE001 - any failure is a test failure
            errors.append(error)

    threads = [threading.Thread(target=connect) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []


def test_adding_an_existing_column_is_tolerated(tmp_path):
    connection = DatabaseConnection(config={"database_path": str(tmp_path / "x.db")}).connect()
    try:
        # A second process may add the column between the check and the ALTER.
        DatabaseConnection._add_column(connection, "PROGRESO_LECCION", "respuestas", "TEXT")
        DatabaseConnection._add_column(connection, "PROGRESO_LECCION", "respuestas", "TEXT")
    finally:
        connection.close()


def test_cached_course_content_is_copied_for_each_caller():
    """The lesson page shuffles the quiz options in place; that must not alter
    the content other requests receive."""
    first = RutaModel.obtener_leccion("variables")
    first["questions"][0][1].clear()
    first["titulo"] = "modificado"

    second = RutaModel.obtener_leccion("variables")

    assert len(second["questions"][0][1]) == 4
    assert second["titulo"] == "Variables y tipos de datos"
