"""Unit tests of AuthService rules (registration, login, level, reset codes) with a fake repository."""

import pytest

from services.auth_service import AuthService


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


def test_reset_code_rejects_unknown_users_and_weak_passwords():
    service = AuthService(FakeUsers())

    assert service.create_reset_code("missing@example.com") == (None, None)
    assert service.reset_password_with_code("missing@example.com", "123456", "short") == "weak"
    assert service.reset_password_with_code("missing@example.com", "123456", "letters-only") == "weak"
    assert service.reset_password_with_code("missing@example.com", "123456", "new-password-1") == "expired"


# Boundary values of the name length (2 to 30 characters after trimming).
@pytest.mark.parametrize(
    "name, accepted",
    [("A", False), ("An", True), ("A" * 30, True), ("A" * 31, False), ("   ", False), ("  Ana  ", True)],
)
def test_name_length_boundaries(name, accepted):
    created, _message = AuthService(FakeUsers()).register(name, "ana@example.com", "password-123")
    assert created is accepted


# Equivalence classes of the e-mail address.
@pytest.mark.parametrize(
    "email, accepted",
    [
        ("ana@example.com", True),
        ("ANA@Example.COM", True),     # normalized to lower case
        ("sin-arroba.com", False),
        ("ana@dominio", False),        # no top-level domain
        ("ana perez@example.com", False),
        ("", False),
    ],
)
def test_email_equivalence_classes(email, accepted):
    created, _message = AuthService(FakeUsers()).register("Ana", email, "password-123")
    assert created is accepted


# Equivalence classes and boundaries of the password rule.
@pytest.mark.parametrize(
    "password, strong",
    [
        ("abc1234", False),      # 7 characters
        ("abcd1234", True),      # 8 characters
        ("abcdefgh", False),     # letters only
        ("12345678", False),     # digits only
        ("ñandú2024", True),     # non-ASCII letters
        ("", False),
        (None, False),
    ],
)
def test_password_rule(password, strong):
    assert AuthService.password_is_strong(password) is strong


def test_duplicate_email_is_rejected_ignoring_case():
    service = AuthService(FakeUsers())
    service.register("Ana", "ana@example.com", "password-123")

    created, message = service.register("Otra", "ANA@example.com", "password-123")

    assert created is False
    assert "ya está registrado" in message


# Decision table of the initial level recommendation (correct answers 0..3).
@pytest.mark.parametrize(
    "answers, level",
    [
        (["", "", ""], "inicial"),
        (["variables", "", ""], "inicial"),
        (["variables", "int", ""], "basico"),
        (["variables", "int", "if"], "intermedio"),
    ],
)
def test_level_recommendation_decision_table(answers, level):
    assert AuthService.recommend_level(answers)["codigo"] == level
