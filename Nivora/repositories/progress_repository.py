import json

from database.database import DatabaseConnection


class ProgressRepository:
    """Persists one row per (student, activity).

    Repeating an activity updates the same row: the number of attempts grows,
    the latest answers are kept so the student can see them again, and a
    lesson that was completed once stays completed (repeating it to review
    never resets the student's progress).
    """

    def __init__(self, database=None):
        self.database = database or DatabaseConnection()

    def find_by_user(self, user_id):
        if not user_id:
            return {}

        connection = self.database.connect()
        try:
            rows = connection.execute(
                """
                SELECT leccion_id, completada, intentada, puntuacion, total
                FROM PROGRESO_LECCION
                WHERE id_persona = ?
                """,
                (user_id,),
            ).fetchall()
            return {
                row["leccion_id"]: {
                    "completada": bool(row["completada"]),
                    "intentada": bool(row["intentada"]),
                    "puntuacion": row["puntuacion"],
                    "total": row["total"],
                }
                for row in rows
            }
        finally:
            connection.close()

    def find_last_answers(self, user_id, lesson_id):
        """Return the answers of the latest attempt, or ``None``."""
        if not user_id:
            return None

        connection = self.database.connect()
        try:
            row = connection.execute(
                """
                SELECT respuestas FROM PROGRESO_LECCION
                WHERE id_persona = ? AND leccion_id = ?
                """,
                (user_id, lesson_id),
            ).fetchone()
        finally:
            connection.close()
        if row is None or not row["respuestas"]:
            return None
        try:
            answers = json.loads(row["respuestas"])
        except (TypeError, ValueError):
            return None
        if not isinstance(answers, list):
            return None
        return [str(answer) for answer in answers]

    def save_activity(self, user_id, lesson_id, activity, answers=None):
        if not user_id:
            return

        connection = self.database.connect()
        try:
            connection.execute(
                """
                INSERT INTO PROGRESO_LECCION
                    (id_persona, leccion_id, completada, intentada, puntuacion,
                     total, intentos, respuestas)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(id_persona, leccion_id) DO UPDATE SET
                    completada = MAX(completada, excluded.completada),
                    intentada = MAX(intentada, excluded.intentada),
                    puntuacion = MAX(puntuacion, excluded.puntuacion),
                    total = excluded.total,
                    intentos = intentos + 1,
                    respuestas = COALESCE(excluded.respuestas, respuestas)
                """,
                (
                    user_id,
                    lesson_id,
                    int(activity.get("completada", False)),
                    int(activity.get("intentada", False)),
                    activity.get("puntuacion", 0),
                    activity.get("total", 0),
                    json.dumps(answers) if answers is not None else None,
                ),
            )
            connection.commit()
        finally:
            connection.close()
