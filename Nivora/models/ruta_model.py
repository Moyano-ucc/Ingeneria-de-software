
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
        "number",
        "positive",
        "even",
        "even_print",
        "odd",
        "odd_print",
        "not_positive",
        "not_positive_print",
    ]

    @classmethod
    def obtener_lecciones(cls):
        """Obtiene las lecciones y sus preguntas desde la base de datos."""
        connection = cls.database.connect()

        try:
            rows = connection.execute(
                """
                SELECT
                    l.id_leccion,
                    l.id_unidad,
                    l.codigo,
                    l.numero,
                    l.titulo,
                    l.contenido,
                    e.pregunta,
                    e.respuesta_correcta,
                    e.opciones
                FROM LECCION AS l
                LEFT JOIN EJERCICIO_LECCION AS e
                    ON e.id_leccion = l.id_leccion
                ORDER BY
                    l.id_unidad,
                    l.numero,
                    e.numero
                """
            ).fetchall()

            lessons = {}

            for row in rows:
                lesson_id = row["codigo"]

                if not lesson_id:
                    lesson_id = f"leccion_{row['id_leccion']}"

                if lesson_id not in lessons:
                    lessons[lesson_id] = {
                        "id": lesson_id,
                        "database_id": row["id_leccion"],
                        "unit_id": row["id_unidad"],
                        "numero": row["numero"],
                        "titulo": row["titulo"],
                        "descripcion": row["contenido"],
                        "answers": [],
                        "questions": [],
                    }

                lesson = lessons[lesson_id]

                if row["pregunta"] is not None:
                    try:
                        options_data = json.loads(row["opciones"] or "[]")
                    except (TypeError, json.JSONDecodeError):
                        options_data = []

                    lesson["answers"].append(
                        row["respuesta_correcta"]
                    )

                    lesson["questions"].append(
                        (
                            row["pregunta"],
                            [
                                (option["value"], option["label"])
                                for option in options_data
                                if isinstance(option, dict)
                                and "value" in option
                                and "label" in option
                            ],
                        )
                    )

            return sorted(
                lessons.values(),
                key=lambda lesson: (
                    lesson["unit_id"],
                    lesson["numero"],
                    lesson["database_id"],
                ),
            )

        finally:
            connection.close()

    @classmethod
    def obtener_rutas(cls, actividades=None):
        """Calcula el progreso y el desbloqueo de cada unidad."""
        actividades = actividades or {}

        connection = cls.database.connect()

        try:
            units = connection.execute(
                """
                SELECT id_unidad, numero, nombre, descripcion
                FROM UNIDAD
                ORDER BY numero
                """
            ).fetchall()
        finally:
            connection.close()

        lessons = cls.obtener_lecciones()

        first_unit_lessons = [
            lesson
            for lesson in lessons
            if lesson["unit_id"] == 1
        ]

        # La Unidad 2 se desbloquea al completar todas las
        # lecciones de la Unidad 1.
        unit_two_unlocked = (
            bool(first_unit_lessons)
            and all(
                cls._is_completed(
                    actividades.get(lesson["id"], {})
                )
                for lesson in first_unit_lessons
            )
        )

        routes = []

        for unit in units:
            unit_id = unit["id_unidad"]

            unit_lessons = [
                lesson
                for lesson in lessons
                if lesson["unit_id"] == unit_id
            ]

            completed_lessons = sum(
                cls._is_completed(
                    actividades.get(lesson["id"], {})
                )
                for lesson in unit_lessons
            )

            completed = completed_lessons
            total_activities = len(unit_lessons)

            # El rompecabezas es una actividad independiente
            # de las cuatro lecciones de la Unidad 2.
            if unit_id == 2:
                puzzle_completed = cls._is_completed(
                    actividades.get("unidad_02_puzzle", {})
                )

                completed += int(puzzle_completed)
                total_activities += 1

            if unit_id == 1:
                unlocked = True
            elif unit_id == 2:
                unlocked = unit_two_unlocked
            else:
                # Las unidades 3 y 4 siguen bloqueadas
                # hasta implementar su contenido.
                unlocked = False

            routes.append(
                {
                    "id": f"{unit['numero']:02d}",
                    "nombre": unit["nombre"],
                    "descripcion": unit["descripcion"],
                    "progreso": f"{completed}/{total_activities}",
                    "estado": (
                        "Completada"
                        if total_activities > 0
                        and completed == total_activities
                        else "Continuar" if unlocked else "Bloqueada"
                    ),
                    "desbloqueada": unlocked,
                }
            )

        return routes

    @classmethod
    def obtener_leccion(cls, lesson_id):
        """Busca una lección por su código."""
        return next(
            (
                lesson
                for lesson in cls.obtener_lecciones()
                if lesson["id"] == lesson_id
            ),
            None,
        )

    @classmethod
    def unidad_dos_desbloqueada(cls, actividades=None):
        """Comprueba si se completaron todas las lecciones de la Unidad 1."""
        actividades = actividades or {}

        first_unit_lessons = [
            lesson
            for lesson in cls.obtener_lecciones()
            if lesson["unit_id"] == 1
        ]

        return (
            bool(first_unit_lessons)
            and all(
                cls._is_completed(
                    actividades.get(lesson["id"], {})
                )
                for lesson in first_unit_lessons
            )
        )

    @staticmethod
    def _is_completed(activity):
        """Admite tanto el formato nuevo como el progreso antiguo."""
        if isinstance(activity, dict):
            return bool(activity.get("completada"))

        return bool(activity)
