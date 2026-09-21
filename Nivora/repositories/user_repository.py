from database.database import DatabaseConnection


class UserRepository:
    def __init__(self, database=None):
        self.database = database or DatabaseConnection()

    def find_by_email(self, email):
        connection = self.database.connect()
        try:
            row = connection.execute(
                """
                SELECT id_persona, nombre, correo, contrasena
                FROM PERSONA
                WHERE correo = ?
                """,
                (email,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()

    def create(self, nombre, email, password_hash):
        connection = self.database.connect()
        try:
            cursor = connection.execute(
                "INSERT INTO PERSONA (nombre, correo, contrasena) VALUES (?, ?, ?)",
                (nombre, email, password_hash),
            )
            connection.execute(
                "INSERT INTO USUARIO (id_persona) VALUES (?)",
                (cursor.lastrowid,),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def update_password(self, user_id, password_hash):
        connection = self.database.connect()
        try:
            connection.execute(
                "UPDATE PERSONA SET contrasena = ? WHERE id_persona = ?",
                (password_hash, user_id),
            )
            connection.commit()
        finally:
            connection.close()
