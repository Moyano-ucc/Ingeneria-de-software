from database.database import AdaptativeConnection


class UsuarioModel:

    db = AdaptativeConnection()

    @classmethod
    def registrar(cls, nombre, email, password):
        conexion = cls.db.connect()

        try:
            usuario = conexion.execute(
                "SELECT id_persona FROM PERSONA WHERE correo = ?",
                (email,)
            ).fetchone()

            if usuario:
                return False, "El correo electrónico ya está registrado"

            cursor = conexion.execute(
                """
                INSERT INTO PERSONA (nombre, correo, contrasena)
                VALUES (?, ?, ?)
                """,
                (nombre, email, password)
            )

            id_persona = cursor.lastrowid

            conexion.execute(
                """
                INSERT INTO USUARIO (id_persona)
                VALUES (?)
                """,
                (id_persona,)
            )

            conexion.commit()

            return True, "Cuenta creada exitosamente"

        except Exception:
            conexion.rollback()
            return False, "Error al crear la cuenta"

        finally:
            conexion.close()

    @classmethod
    def autenticar(cls, email, password):
        conexion = cls.db.connect()

        try:
            usuario = conexion.execute(
                """
                SELECT
                    PERSONA.id_persona,
                    PERSONA.nombre,
                    PERSONA.correo
                FROM PERSONA
                INNER JOIN USUARIO
                    ON PERSONA.id_persona = USUARIO.id_persona
                WHERE PERSONA.correo = ?
                AND PERSONA.contrasena = ?
                """,
                (email, password)
            ).fetchone()

            if usuario:
                return dict(usuario)

            return None

        finally:
            conexion.close()