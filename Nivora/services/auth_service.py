import re

from werkzeug.security import check_password_hash, generate_password_hash

from repositories.user_repository import UserRepository


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class AuthService:
    def __init__(self, users=None):
        self.users = users or UserRepository()

    def register(self, name, email, password, quiz_answers=None):
        name = (name or "").strip()
        email = (email or "").strip().lower()

        if not 2 <= len(name) <= 30:
            return False, "El nombre debe tener entre 2 y 30 caracteres"
        if not EMAIL_PATTERN.fullmatch(email):
            return False, "Introduce un correo electrónico válido"
        if len(password or "") < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        if self.users.find_by_email(email):
            return False, "El correo electrónico ya está registrado"

        try:
            self.users.create(name, email, generate_password_hash(password))
        except Exception:
            return False, "Error al crear la cuenta"
        return True, "Cuenta creada exitosamente"

    @staticmethod
    def recommend_level(quiz_answers):
        correct_answers = ["variables", "int", "if"]
        score = sum(
            answer == correct
            for answer, correct in zip(quiz_answers, correct_answers)
        )
        if score == 3:
            return {
                "codigo": "intermedio",
                "puntuacion": score,
                "titulo": "Puedes comenzar con Variables y tipos de datos",
                "detalle": "Respondiste correctamente las tres preguntas. Empieza con esta lección para conocer la ruta de Nivora y después avanza a Control de flujo.",
                "leccion": "variables",
            }
        if score == 2:
            return {
                "codigo": "basico",
                "puntuacion": score,
                "titulo": "Comienza con Variables y tipos de datos",
                "detalle": "Tienes buenas bases. Te recomendamos reforzar variables antes de continuar.",
                "leccion": "variables",
            }
        return {
            "codigo": "inicial",
            "puntuacion": score,
            "titulo": "Te recomendamos empezar desde cero",
            "detalle": "Comenzaremos con variables y tipos de datos, paso a paso.",
            "leccion": "variables",
        }

    @staticmethod
    def grade_lesson(answers):
        correct_answers = ["nombre", "int", "True"]
        score = sum(
            answer == correct
            for answer, correct in zip(answers, correct_answers)
        )
        return score, len(correct_answers)

    def authenticate(self, email, password):
        user = self.users.find_by_email((email or "").strip().lower())
        if not user:
            return None

        stored_password = user["contrasena"]
        valid = check_password_hash(stored_password, password or "")
        if not valid and stored_password == (password or ""):
            valid = True
            self.users.update_password(
                user["id_persona"], generate_password_hash(password)
            )
        if not valid:
            return None

        return {
            "id_persona": user["id_persona"],
            "nombre": user["nombre"],
            "email": user["correo"],
        }
