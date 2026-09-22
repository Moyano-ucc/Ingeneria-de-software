from database.database import DatabaseConnection


class ProgressRepository:
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

    def save_activity(self, user_id, lesson_id, activity):
        if not user_id:
            return

        connection = self.database.connect()
        try:
            connection.execute(
                """
                INSERT INTO PROGRESO_LECCION
                    (id_persona, leccion_id, completada, intentada, puntuacion, total)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id_persona, leccion_id) DO UPDATE SET
                    completada = excluded.completada,
                    intentada = excluded.intentada,
                    puntuacion = excluded.puntuacion,
                    total = excluded.total
                """,
                (
                    user_id,
                    lesson_id,
                    int(activity.get("completada", False)),
                    int(activity.get("intentada", False)),
                    activity.get("puntuacion", 0),
                    activity.get("total", 0),
                ),
            )
            connection.commit()
        finally:
            connection.close()