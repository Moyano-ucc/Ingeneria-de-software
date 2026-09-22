import json

from database.database import DatabaseConnection


class RutaModel:
    database = DatabaseConnection()

    @classmethod
    def obtener_lecciones(cls):
        connection = cls.database.connect()
        try:
            rows = connection.execute(
                """
                SELECT l.id_leccion, l.codigo, l.numero, l.titulo, l.contenido,
                       e.pregunta, e.respuesta_correcta, e.opciones
                FROM LECCION l
                LEFT JOIN EJERCICIO_LECCION e ON e.id_leccion = l.id_leccion
                ORDER BY l.numero, e.numero
                """
            ).fetchall()
            lessons = {}
            for row in rows:
                lesson = lessons.setdefault(row["codigo"], {
                    "id": row["codigo"],
                    "numero": row["numero"],
                    "titulo": row["titulo"],
                    "descripcion": row["contenido"],
                    "answers": [],
                    "questions": [],
                })
                if row["pregunta"] is not None:
                    lesson["answers"].append(row["respuesta_correcta"])
                    lesson["questions"].append((
                        row["pregunta"],
                        [
                            (option["value"], option["label"])
                            for option in json.loads(row["opciones"])
                        ],
                    ))
            return list(lessons.values())
        finally:
            connection.close()

    @classmethod
    def obtener_rutas(cls, actividades=None):
        actividades = actividades or {}
        connection = cls.database.connect()
        try:
            units = connection.execute(
                "SELECT id_unidad, numero, nombre, descripcion FROM UNIDAD ORDER BY numero"
            ).fetchall()
            lessons = cls.obtener_lecciones()
            routes = []
            for unit in units:
                unit_lessons = [
                    lesson for lesson in lessons if lesson["numero"] <= 4 and (
                        unit["id_unidad"] == 1
                    )
                ] if unit["id_unidad"] == 1 else []
                completed = sum(
                    cls._is_completed(actividades.get(lesson["id"], {}))
                    for lesson in unit_lessons
                )
                routes.append({
                    "id": f"{unit['numero']:02d}",
                    "nombre": unit["nombre"],
                    "descripcion": unit["descripcion"],
                    "progreso": f"{completed}/{len(unit_lessons) or 4}",
                    "estado": "Continuar" if unit["id_unidad"] == 1 else "Bloqueada",
                })
            return routes
        finally:
            connection.close()

    @classmethod
    def obtener_leccion(cls, lesson_id):
        return next(
            (lesson for lesson in cls.obtener_lecciones() if lesson["id"] == lesson_id),
            None,
        )

    @staticmethod
    def _is_completed(activity):
        if isinstance(activity, dict):
            return bool(activity.get("completada"))
        return bool(activity)
