import time

from database.database import DatabaseConnection


class ApunteRepository:
    """Personal notes of each student, per lesson.

    Every query filters by ``id_persona``: a student can only read or change
    their own notes.
    """

    COLUMNS = "id_apunte, leccion_id, contenido, destacado, creado, actualizado"

    def __init__(self, database=None):
        self.database = database or DatabaseConnection()

    @staticmethod
    def _to_dict(row):
        if row is None:
            return None
        return {
            "id": row["id_apunte"],
            "leccion": row["leccion_id"],
            "contenido": row["contenido"],
            "destacado": bool(row["destacado"]),
            "creado": row["creado"],
            "actualizado": row["actualizado"],
        }

    def list(self, user_id, leccion=None):
        query = f"SELECT {self.COLUMNS} FROM APUNTE WHERE id_persona = ?"
        params = [user_id]
        if leccion:
            query += " AND leccion_id = ?"
            params.append(leccion)
        query += " ORDER BY destacado DESC, actualizado DESC"
        connection = self.database.connect()
        try:
            return [self._to_dict(row) for row in connection.execute(query, params).fetchall()]
        finally:
            connection.close()

    def get(self, user_id, apunte_id):
        connection = self.database.connect()
        try:
            row = connection.execute(
                f"SELECT {self.COLUMNS} FROM APUNTE WHERE id_persona = ? AND id_apunte = ?",
                (user_id, apunte_id),
            ).fetchone()
            return self._to_dict(row)
        finally:
            connection.close()

    def create(self, user_id, leccion, contenido, destacado=False):
        now = time.time()
        connection = self.database.connect()
        try:
            cursor = connection.execute(
                """
                INSERT INTO APUNTE (id_persona, leccion_id, contenido, destacado, creado, actualizado)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, leccion, contenido, int(destacado), now, now),
            )
            connection.commit()
            apunte_id = cursor.lastrowid
        finally:
            connection.close()
        return self.get(user_id, apunte_id)

    def update(self, user_id, apunte_id, **fields):
        """Update the given fields; return the note or ``None`` if it is not theirs."""
        allowed = {"leccion": "leccion_id", "contenido": "contenido", "destacado": "destacado"}
        changes = {allowed[key]: value for key, value in fields.items() if key in allowed}
        if "destacado" in changes:
            changes["destacado"] = int(changes["destacado"])
        assignments = ", ".join(f"{column} = ?" for column in changes)
        connection = self.database.connect()
        try:
            cursor = connection.execute(
                f"UPDATE APUNTE SET {assignments + ', ' if assignments else ''}actualizado = ? "
                "WHERE id_persona = ? AND id_apunte = ?",
                (*changes.values(), time.time(), user_id, apunte_id),
            )
            connection.commit()
            if cursor.rowcount == 0:
                return None
        finally:
            connection.close()
        return self.get(user_id, apunte_id)

    def delete(self, user_id, apunte_id):
        connection = self.database.connect()
        try:
            cursor = connection.execute(
                "DELETE FROM APUNTE WHERE id_persona = ? AND id_apunte = ?",
                (user_id, apunte_id),
            )
            connection.commit()
            return cursor.rowcount > 0
        finally:
            connection.close()
