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

    def create_password_reset(self, user_id, token_hash, expires_at):
        connection = self.database.connect()
        try:
            connection.execute("DELETE FROM PASSWORD_RESET WHERE id_persona = ?", (user_id,))
            connection.execute(
                "INSERT INTO PASSWORD_RESET (token_hash, id_persona, expires_at) VALUES (?, ?, ?)",
                (token_hash, user_id, expires_at),
            )
            connection.commit()
        finally:
            connection.close()

    def update_password_with_reset(self, token_hash, password_hash, now):
        connection = self.database.connect()
        try:
            reset = connection.execute(
                """
                SELECT id_persona FROM PASSWORD_RESET
                WHERE token_hash = ? AND expires_at > ? AND used_at IS NULL
                """,
                (token_hash, now),
            ).fetchone()
            if reset is None:
                return False
            connection.execute(
                "UPDATE PERSONA SET contrasena = ? WHERE id_persona = ?",
                (password_hash, reset["id_persona"]),
            )
            connection.execute(
                "UPDATE PASSWORD_RESET SET used_at = ? WHERE token_hash = ?",
                (now, token_hash),
            )
            connection.commit()
            return True
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
