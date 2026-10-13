import json

from database.database import DatabaseConnection


class RutaModel:
    database = DatabaseConnection()
    PUZZLE_PIECES = [
        {"id": "number", "code": "numero = 8"},
        {"id": "positive", "code": "if numero > 0:"},
        {"id": "even", "code": "    if numero % 2 == 0:"},
        {"id": "even_print", "code": "        print('positivo y par')"},
        {"id": "odd", "code": "    else:"},
        {"id": "odd_print", "code": "        print('positivo e impar')"},
        {"id": "not_positive", "code": "else:"},
        {"id": "not_positive_print", "code": "    print('no positivo')"},
    ]
    PUZZLE_SOLUTION = [
        "number", "positive", "even", "even_print", "odd", "odd_print",
        "not_positive", "not_positive_print",
    ]

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
                ORDER BY l.numero, e.numero
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
        actividades = actividades or {}
        connection = cls.database.connect()
        try:
            units = connection.execute(
                "SELECT id_unidad, numero, nombre, descripcion FROM UNIDAD ORDER BY numero"
            ).fetchall()
            lessons = cls.obtener_lecciones()
            first_unit_lessons = [lesson for lesson in lessons if lesson["unit_id"] == 1]
            unit_two_unlocked = bool(first_unit_lessons) and all(
                cls._is_completed(actividades.get(lesson["id"], {}))
                for lesson in first_unit_lessons
            )
            routes = []
            for unit in units:
                unit_lessons = [
                    lesson for lesson in lessons
                    if lesson["unit_id"] == unit["id_unidad"]
                ]
                completed = sum(
                    cls._is_completed(actividades.get(lesson["id"], {}))
                    for lesson in unit_lessons
                )
                unlocked = unit["id_unidad"] == 1 or (
                    unit["id_unidad"] == 2 and unit_two_unlocked
                )
                if unit["id_unidad"] == 2:
                    completed = int(
                        cls._is_completed(actividades.get("unidad_02_puzzle", {}))
                    )
                    lesson_count = 1
                else:
                    lesson_count = len(unit_lessons) or 4
                routes.append({
                    "id": f"{unit['numero']:02d}",
                    "nombre": unit["nombre"],
                    "descripcion": unit["descripcion"],
                    "progreso": f"{completed}/{lesson_count}",
                    "estado": "Continuar" if unlocked else "Bloqueada",
                    "desbloqueada": unlocked,
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

    @classmethod
    def unidad_dos_desbloqueada(cls, actividades=None):
        actividades = actividades or {}
        first_unit_lessons = [
            lesson for lesson in cls.obtener_lecciones() if lesson["unit_id"] == 1
        ]
        return bool(first_unit_lessons) and all(
            cls._is_completed(actividades.get(lesson["id"], {}))
            for lesson in first_unit_lessons
        )

    @staticmethod
    def _is_completed(activity):
        if isinstance(activity, dict):
            return bool(activity.get("completada"))
        return bool(activity)
