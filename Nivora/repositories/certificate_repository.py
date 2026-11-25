import secrets
import sqlite3
import time

from database.database import DatabaseConnection


class CertificateRepository:
    """One completion certificate per student, issued only once.

    The issue date and the code are stored the first time the certificate is
    generated, so they never change when the student opens it again.
    """

    def __init__(self, database=None):
        self.database = database or DatabaseConnection()

    @staticmethod
    def _new_code():
        # Unambiguous characters (no 0/O or 1/I), e.g. NIV-7KQ4-M2XD.
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        chars = "".join(secrets.choice(alphabet) for _ in range(8))
        return f"NIV-{chars[:4]}-{chars[4:]}"

    def find_by_user(self, user_id):
        connection = self.database.connect()
        try:
            row = connection.execute(
                "SELECT codigo, fecha_emision FROM CERTIFICADO WHERE id_persona = ?",
                (user_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()

    def issue(self, user_id):
        """Return the student's certificate, creating it the first time."""
        existing = self.find_by_user(user_id)
        if existing:
            return existing
        connection = self.database.connect()
        try:
            for _ in range(5):
                try:
                    connection.execute(
                        "INSERT INTO CERTIFICADO (id_persona, codigo, fecha_emision) VALUES (?, ?, ?)",
                        (user_id, self._new_code(), time.time()),
                    )
                    connection.commit()
                    break
                except sqlite3.IntegrityError:
                    connection.rollback()
                    # Another request issued it first, or the code collided.
                    if self.find_by_user(user_id):
                        break
        finally:
            connection.close()
        return self.find_by_user(user_id)

    def find_by_code(self, code):
        connection = self.database.connect()
        try:
            row = connection.execute(
                """
                SELECT c.codigo, c.fecha_emision, p.nombre
                FROM CERTIFICADO c
                JOIN PERSONA p ON p.id_persona = c.id_persona
                WHERE c.codigo = ?
                """,
                ((code or "").strip().upper(),),
            ).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()
