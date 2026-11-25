from database.database import DatabaseConnection
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from werkzeug.security import check_password_hash, generate_password_hash


class FakeUsers:
    def __init__(self):
        self.users = {}
        self.next_id = 1
        self.resets = {}

    def find_by_email(self, email):
        return self.users.get(email)

    def create(self, name, email, password_hash):
        self.users[email] = {
            "id_persona": self.next_id,
            "nombre": name,
            "correo": email,
            "contrasena": password_hash,
        }
        self.next_id += 1

    def update_password(self, user_id, password_hash):
        for user in self.users.values():
            if user["id_persona"] == user_id:
                user["contrasena"] = password_hash

    def create_password_reset(self, user_id, token_hash, expires_at):
        self.resets[user_id] = {"token_hash": token_hash, "expires_at": expires_at}

    def consume_reset_code(self, user_id, code_hash, password_hash, now, max_attempts):
        reset = self.resets.get(user_id)
        if not reset or reset["expires_at"] <= now or reset.get("used_at"):
            return "expired"
        if reset["token_hash"] != code_hash:
            return "invalid"
        for user in self.users.values():
            if user["id_persona"] == user_id:
                user["contrasena"] = password_hash
        reset["used_at"] = now
        return "ok"


def test_register_and_authenticate_hashes_password():
    users = FakeUsers()
    service = AuthService(users)

    created, _message = service.register("Ana", "ANA@example.com", "password-123")

    assert created is True
    assert users.users["ana@example.com"]["contrasena"] != "password-123"
    assert service.authenticate("ana@example.com", "password-123")["nombre"] == "Ana"
    assert service.authenticate("ana@example.com", "incorrecta") is None


def test_register_rejects_short_password_and_invalid_email():
    service = AuthService(FakeUsers())

    assert service.register("Ana", "not-an-email", "password-123")[0] is False
    assert service.register("Ana", "ana@example.com", "short")[0] is False


def test_registration_requires_a_matching_letter_and_number_password():
    service = AuthService(FakeUsers())

    assert service.register("Ana", "ana@example.com", "letters-only")[0] is False
    assert service.register("Ana", "ana@example.com", "12345678")[0] is False
    assert service.register(
        "Ana",
        "ana@example.com",
        "clave1234",
        "clave12345",
    )[0] is False


def test_recommendation_uses_quiz_score():
    assert AuthService.recommend_level(["", "", ""])["codigo"] == "inicial"
    assert AuthService.recommend_level(["variables", "int", "no"])["codigo"] == "basico"
    advanced = AuthService.recommend_level(["variables", "int", "if"])
    assert advanced["codigo"] == "intermedio"
    assert advanced["leccion"] == "variables"


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


def test_reset_code_rejects_unknown_users_and_weak_passwords():
    service = AuthService(FakeUsers())

    assert service.create_reset_code("missing@example.com") == (None, None)
    assert service.reset_password_with_code("missing@example.com", "123456", "short") == "weak"
    assert service.reset_password_with_code("missing@example.com", "123456", "letters-only") == "weak"
    assert service.reset_password_with_code("missing@example.com", "123456", "new-password-1") == "expired"


def test_database_creates_a_custom_parent_directory(tmp_path):
    database_path = tmp_path / "azure-data" / "nivora.db"
    database = DatabaseConnection(config={"database_path": str(database_path)})

    connection = database.connect()
    connection.close()

    assert database_path.exists()
