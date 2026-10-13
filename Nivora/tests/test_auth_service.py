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
        self.resets[token_hash] = {"id_persona": user_id, "expires_at": expires_at}

    def update_password_with_reset(self, token_hash, password_hash, now):
        reset = self.resets.get(token_hash)
        if not reset or reset["expires_at"] <= now or reset.get("used_at"):
            return False
        for user in self.users.values():
            if user["id_persona"] == reset["id_persona"]:
                user["contrasena"] = password_hash
                reset["used_at"] = now
                return True
        return False


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


def test_recommendation_uses_quiz_score():
    assert AuthService.recommend_level(["", "", ""])["codigo"] == "inicial"
    assert AuthService.recommend_level(["variables", "int", "no"])["codigo"] == "basico"
    advanced = AuthService.recommend_level(["variables", "int", "if"])
    assert advanced["codigo"] == "intermedio"
    assert advanced["leccion"] == "variables"


def test_lesson_requires_two_correct_answers():
    assert AuthService.grade_lesson(["nombre", "int", "wrong"]) == (2, 3)
    assert AuthService.grade_lesson(["wrong", "wrong", "wrong"]) == (0, 3)


def test_password_reset_is_single_use_and_persists_in_fresh_sqlite(tmp_path):
    database = DatabaseConnection(config={"database_path": str(tmp_path / "nivora.db")})
    users = UserRepository(database)
    users.create("Ana", "ana@example.com", generate_password_hash("old-password"))
    service = AuthService(users)

    token = service.create_password_reset("ANA@example.com", ttl=60)

    assert token
    assert service.reset_password(token, "new-password") is True
    assert check_password_hash(users.find_by_email("ana@example.com")["contrasena"], "new-password")
    assert service.reset_password(token, "another-password") is False


def test_password_reset_rejects_unknown_users_and_short_passwords():
    service = AuthService(FakeUsers())

    assert service.create_password_reset("missing@example.com") is None
    assert service.reset_password("invalid-token", "short") is False
