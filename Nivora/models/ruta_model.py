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
    LESSON_MATERIAL = {
        "variables": {
            "explicacion": "Una variable nombra un dato para poder reutilizarlo. Python infiere el tipo del valor asignado.",
            "ejemplo": 'nombre = "Ana"\nedad = 20\nactivo = True\nprint(nombre, edad, activo)',
        },
        "operadores": {
            "explicacion": "Los operadores aritméticos calculan valores y los operadores de comparación producen resultados booleanos.",
            "ejemplo": "total = 3 + 4\nes_mayor = total > 5\nes_igual = total == 7",
        },
        "entrada_salida": {
            "explicacion": "print muestra información. input recibe texto; conviértelo cuando necesites un número.",
            "ejemplo": 'nombre = input("Tu nombre: ")\nedad = int(input("Tu edad: "))\nprint(f"Hola {nombre}, tienes {edad}")',
        },
        "repaso_fundamentos": {
            "explicacion": "Combina variables, conversiones, operadores y salida para resolver un problema completo.",
            "ejemplo": 'precio = float(input("Precio: "))\ncantidad = int(input("Cantidad: "))\nprint(f"Total: {precio * cantidad}")',
        },
        "condicionales": {
            "explicacion": "if ejecuta un bloque cuando una condición es verdadera. elif y else permiten elegir otras rutas.",
            "ejemplo": "edad = 18\nif edad >= 18:\n    print('Mayor de edad')\nelse:\n    print('Menor de edad')",
        },
        "while": {
            "explicacion": "while repite un bloque mientras la condición siga siendo verdadera. Actualiza la condición para evitar ciclos infinitos.",
            "ejemplo": "contador = 3\nwhile contador > 0:\n    print(contador)\n    contador -= 1",
        },
        "for": {
            "explicacion": "for recorre los elementos de una secuencia. range genera una secuencia de números.",
            "ejemplo": "for numero in range(1, 4):\n    print(numero)\n\nfrutas = ['pera', 'uva']\nfor fruta in frutas:\n    print(fruta)",
        },
        "control_rompecabezas": {
            "explicacion": "Anida condicionales para comprobar más de una regla y mantener cada caso fácil de entender.",
            "ejemplo": "numero = 8\nif numero > 0:\n    if numero % 2 == 0:\n        print('positivo y par')\n    else:\n        print('positivo e impar')\nelse:\n    print('no positivo')",
        },
        "listas": {
            "explicacion": "Las listas guardan varios valores ordenados. Se pueden consultar por índice y modificar.",
            "ejemplo": "frutas = ['pera', 'uva']\nfrutas.append('mango')\nprint(frutas[0])\nprint(len(frutas))",
        },
        "estructuras": {
            "explicacion": "Las tuplas representan colecciones que no cambian; los diccionarios guardan valores asociados a claves.",
            "ejemplo": "coordenada = (4, 7)\nestudiante = {'nombre': 'Ana', 'edad': 20}\nprint(coordenada[0])\nprint(estudiante['nombre'])",
        },
        "recorrido": {
            "explicacion": "Recorre listas y diccionarios con for para procesar cada elemento o cada par clave-valor.",
            "ejemplo": "notas = [8, 9, 10]\nfor nota in notas:\n    print(nota)\n\nestudiante = {'nombre': 'Ana', 'edad': 20}\nfor clave, valor in estudiante.items():\n    print(clave, valor)",
        },
        "proyecto_estructuras": {
            "explicacion": "Combina listas y diccionarios para representar registros y calcular resultados.",
            "ejemplo": "notas = {'Ana': [8, 9], 'Luis': [7, 10]}\nfor nombre, valores in notas.items():\n    promedio = sum(valores) / len(valores)\n    print(nombre, promedio)",
        },
        "funciones": {
            "explicacion": "Una función agrupa instrucciones reutilizables. def la declara y los paréntesis la ejecutan.",
            "ejemplo": "def saludar():\n    print('Hola')\n\nsaludar()",
        },
        "parametros": {
            "explicacion": "Los parámetros reciben datos y return devuelve un resultado al lugar donde se llamó la función.",
            "ejemplo": "def sumar(a, b):\n    return a + b\n\nresultado = sumar(3, 4)\nprint(resultado)",
        },
        "alcance": {
            "explicacion": "Las variables creadas dentro de una función son locales. Recibe valores como parámetros para evitar dependencias globales.",
            "ejemplo": "def calcular_total(precio, cantidad):\n    total = precio * cantidad\n    return total\n\nprint(calcular_total(5, 3))",
        },
        "proyecto_final": {
            "explicacion": "Divide un programa en funciones pequeñas: una recibe datos, otra calcula y otra presenta el resultado.",
            "ejemplo": "def calcular_promedio(notas):\n    return sum(notas) / len(notas)\n\ndef mostrar_resultado(nombre, notas):\n    promedio = calcular_promedio(notas)\n    print(f'{nombre}: {promedio:.1f}')\n\nmostrar_resultado('Ana', [8, 9, 10])",
        },
    }

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
        actividades = actividades or {}
        connection = cls.database.connect()
        try:
            units = connection.execute(
                "SELECT id_unidad, numero, nombre, descripcion FROM UNIDAD ORDER BY numero"
            ).fetchall()
            lessons = cls.obtener_lecciones()
            first_unit_lessons = [lesson for lesson in lessons if lesson["unit_id"] == 1]
            second_unit_lessons = [lesson for lesson in lessons if lesson["unit_id"] == 2]
            third_unit_lessons = [lesson for lesson in lessons if lesson["unit_id"] == 3]
            unit_two_unlocked = bool(first_unit_lessons) and all(
                cls.actividad_completada(actividades.get(lesson["id"], {}))
                for lesson in first_unit_lessons
            )
            unit_three_unlocked = bool(second_unit_lessons) and all(
                cls.actividad_completada(actividades.get(lesson["id"], {}))
                for lesson in second_unit_lessons
            ) and cls.actividad_completada(actividades.get("unidad_02_puzzle", {}))
            unit_four_unlocked = bool(third_unit_lessons) and all(
                cls.actividad_completada(actividades.get(lesson["id"], {}))
                for lesson in third_unit_lessons
            )
            routes = []
            for unit in units:
                unit_lessons = [
                    lesson for lesson in lessons
                    if lesson["unit_id"] == unit["id_unidad"]
                ]
                completed = sum(
                    cls.actividad_completada(actividades.get(lesson["id"], {}))
                    for lesson in unit_lessons
                )
                unlocked = unit["id_unidad"] == 1
                if unit["id_unidad"] == 2:
                    unlocked = unit_two_unlocked
                elif unit["id_unidad"] == 3:
                    unlocked = unit_three_unlocked
                elif unit["id_unidad"] == 4:
                    unlocked = unit_four_unlocked
                if unit["id_unidad"] == 2:
                    completed = sum(
                        cls.actividad_completada(actividades.get(lesson["id"], {}))
                        for lesson in unit_lessons
                    ) + int(
                        cls.actividad_completada(actividades.get("unidad_02_puzzle", {}))
                    )
                    lesson_count = len(unit_lessons) + 1
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
            cls.actividad_completada(actividades.get(lesson["id"], {}))
            for lesson in first_unit_lessons
        )

    @staticmethod
    def actividad_completada(activity):
        if isinstance(activity, dict):
            return bool(activity.get("completada"))
        return bool(activity)
