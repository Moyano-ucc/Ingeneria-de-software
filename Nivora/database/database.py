import os
import sqlite3


class DatabaseConnection:
    def __init__(self, db_type="sqlite", config=None):
        self.db_type = db_type
        self.config = config or {}

    def connect(self):
        if self.db_type != "sqlite":
            raise ValueError("Tipo de base de datos no soportado")

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        database = self.config.get("database_path") or os.environ.get(
            "NIVORA_DATABASE_PATH",
            os.path.join(base_dir, "database", "nivora.db"),
        )
        connection = sqlite3.connect(database, timeout=10)
        connection.row_factory = sqlite3.Row
        self._initialize_schema(connection)
        return connection

    @staticmethod
    def _initialize_schema(connection):
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS PROGRESO_LECCION (
                id_persona INTEGER NOT NULL,
                leccion_id TEXT NOT NULL,
                completada INTEGER NOT NULL DEFAULT 0,
                intentada INTEGER NOT NULL DEFAULT 0,
                puntuacion INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (id_persona, leccion_id)
            );
            CREATE TABLE IF NOT EXISTS UNIDAD (
                id_unidad INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                numero INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS LECCION (
                id_leccion INTEGER PRIMARY KEY,
                titulo TEXT NOT NULL,
                contenido TEXT NOT NULL,
                numero INTEGER NOT NULL,
                id_unidad INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS EJERCICIO (
                id_ejercicio INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                dificultad TEXT NOT NULL,
                codigo_inicial TEXT,
                solucion_esperada TEXT,
                id_unidad INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS EJERCICIO_LECCION (
                id_ejercicio INTEGER PRIMARY KEY,
                id_leccion INTEGER NOT NULL,
                numero INTEGER NOT NULL,
                pregunta TEXT NOT NULL,
                respuesta_correcta TEXT NOT NULL,
                opciones TEXT NOT NULL
            );
            """
        )
        lesson_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(LECCION)").fetchall()
        }
        if "codigo" not in lesson_columns:
            connection.execute("ALTER TABLE LECCION ADD COLUMN codigo TEXT")

        units = [
            (1, "Fundamentos de Python", "Aprende variables, tipos de datos, operadores y entrada y salida de datos.", 1),
            (2, "Control de flujo", "Aprende a utilizar condicionales y ciclos para controlar tus programas.", 2),
            (3, "Listas y estructuras", "Aprende a trabajar con listas y otras estructuras para organizar información.", 3),
            (4, "Funciones", "Crea funciones para organizar y reutilizar tu código.", 4),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO UNIDAD (id_unidad, nombre, descripcion, numero) VALUES (?, ?, ?, ?)",
            units,
        )

        lessons = [
            (1, "Variables y tipos de datos", "Guarda información y reconoce los tipos básicos de Python.", 1, 1, "variables"),
            (2, "Operadores y expresiones", "Realiza operaciones y compara valores.", 2, 1, "operadores"),
            (3, "Entrada y salida de datos", "Muestra información y recibe datos del usuario.", 3, 1, "entrada_salida"),
            (4, "Repaso de fundamentos", "Comprueba lo aprendido en la primera ruta.", 4, 1, "repaso_fundamentos"),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO LECCION (id_leccion, titulo, contenido, numero, id_unidad, codigo) VALUES (?, ?, ?, ?, ?, ?)",
            lessons,
        )

        exercises = [
            (1, "Pregunta 1", "¿Qué nombre tiene el valor en nombre = \"Ana\"?", "nombre"),
            (2, "Pregunta 2", "¿Qué tipo de dato es 20?", "int"),
            (3, "Pregunta 3", "¿Cuál representa verdadero o falso?", "True"),
            (4, "Pregunta 1", "¿Cuál es el resultado de 3 + 4?", "7"),
            (5, "Pregunta 2", "¿Qué devuelve 5 > 2?", "True"),
            (6, "Pregunta 3", "¿Qué operador compara igualdad?", "=="),
            (7, "Pregunta 1", "¿Qué función muestra texto?", "print"),
            (8, "Pregunta 2", "¿Qué función recibe datos?", "input"),
            (9, "Pregunta 3", "¿Qué devuelve input normalmente?", "texto"),
            (10, "Pregunta 1", "¿Qué estructura guarda varios valores ordenados?", "lista"),
            (11, "Pregunta 2", "¿Qué función obtiene la cantidad de elementos?", "len"),
            (12, "Pregunta 3", "¿Qué método agrega un elemento a una lista?", "append"),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO EJERCICIO (id_ejercicio, titulo, descripcion, dificultad, solucion_esperada, id_unidad) VALUES (?, ?, ?, 'basico', ?, 1)",
            [(number, title, question, answer) for number, title, question, answer in exercises],
        )

        options = [
            (1, 1, 1, "nombre", '[{"value": "nombre", "label": "nombre"}, {"value": "Ana", "label": "Ana"}]'),
            (2, 1, 2, "int", '[{"value": "int", "label": "int"}, {"value": "str", "label": "str"}]'),
            (3, 1, 3, "True", '[{"value": "True", "label": "True"}, {"value": "10", "label": "10"}]'),
            (4, 2, 1, "7", '[{"value": "7", "label": "7"}, {"value": "12", "label": "12"}]'),
            (5, 2, 2, "True", '[{"value": "True", "label": "True"}, {"value": "False", "label": "False"}]'),
            (6, 2, 3, "==", '[{"value": "==", "label": "=="}, {"value": "=", "label": "="}]'),
            (7, 3, 1, "print", '[{"value": "print", "label": "print"}, {"value": "input", "label": "input"}]'),
            (8, 3, 2, "input", '[{"value": "input", "label": "input"}, {"value": "print", "label": "print"}]'),
            (9, 3, 3, "texto", '[{"value": "texto", "label": "texto"}, {"value": "int", "label": "int"}]'),
            (10, 4, 1, "lista", '[{"value": "lista", "label": "lista"}, {"value": "if", "label": "if"}]'),
            (11, 4, 2, "len", '[{"value": "len", "label": "len"}, {"value": "sum", "label": "sum"}]'),
            (12, 4, 3, "append", '[{"value": "append", "label": "append"}, {"value": "add", "label": "add"}]'),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO EJERCICIO_LECCION (id_ejercicio, id_leccion, numero, pregunta, respuesta_correcta, opciones) VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    exercise_id,
                    lesson_id,
                    number,
                    next(item[2] for item in exercises if item[0] == exercise_id),
                    correct_answer,
                    option_data,
                )
                for exercise_id, lesson_id, number, correct_answer, option_data in options
            ],
        )
        connection.commit()
