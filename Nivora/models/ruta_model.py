import json

from database.database import DatabaseConnection
from models.contenido_lecciones import LESSON_MATERIAL


class RutaModel:
    database = DatabaseConnection()
    LESSON_MATERIAL = LESSON_MATERIAL

    @classmethod
    def obtener_material_leccion(cls, lesson_id):
        return cls.LESSON_MATERIAL.get(lesson_id)

    @classmethod
    def obtener_lecciones(cls):
        connection = cls.database.connect()
        try:
            rows = connection.execute(
                """
                SELECT l.id_leccion, l.id_unidad, l.codigo, l.numero, l.titulo, l.contenido,
                       e.pregunta, e.respuesta_correcta, e.opciones
                FROM LECCION l
                LEFT JOIN EJERCICIO_LECCION e ON e.id_leccion = l.id_leccion
                ORDER BY l.id_unidad, l.numero, e.numero
                """
            ).fetchall()
            lessons = {}
            for row in rows:
                lesson = lessons.setdefault(row["codigo"], {
                    "id": row["codigo"],
                    "unit_id": row["id_unidad"],
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
        """Units in order. A unit unlocks when every lesson of the previous one
        is completed; the first unit is always open."""
        actividades = actividades or {}
        connection = cls.database.connect()
        try:
            units = connection.execute(
                "SELECT id_unidad, numero, nombre, descripcion FROM UNIDAD ORDER BY numero"
            ).fetchall()
        finally:
            connection.close()

        lessons = cls.obtener_lecciones()
        routes = []
        previous_completed = True
        for unit in units:
            unit_lessons = [
                lesson for lesson in lessons if lesson["unit_id"] == unit["id_unidad"]
            ]
            completed = sum(
                cls.actividad_completada(actividades.get(lesson["id"], {}))
                for lesson in unit_lessons
            )
            unlocked = previous_completed
            routes.append({
                "id": f"{unit['numero']:02d}",
                "nombre": unit["nombre"],
                "descripcion": unit["descripcion"],
                "progreso": f"{completed}/{len(unit_lessons)}",
                "completadas": completed,
                "total": len(unit_lessons),
                "estado": "Continuar" if unlocked else "Bloqueada",
                "desbloqueada": unlocked,
            })
            previous_completed = bool(unit_lessons) and completed == len(unit_lessons)
        return routes

    @classmethod
    def obtener_leccion(cls, lesson_id):
        return next(
            (lesson for lesson in cls.obtener_lecciones() if lesson["id"] == lesson_id),
            None,
        )

    @staticmethod
    def actividad_completada(activity):
        if isinstance(activity, dict):
            return bool(activity.get("completada"))
        return bool(activity)
