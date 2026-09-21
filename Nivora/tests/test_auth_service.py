from services.auth_service import AuthService


class FakeUsers:
    def __init__(self):
        self.users = {}
        self.next_id = 1

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
