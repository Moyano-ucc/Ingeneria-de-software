import json
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
        parent_directory = os.path.dirname(os.path.abspath(database))
        os.makedirs(parent_directory, exist_ok=True)
        connection = sqlite3.connect(database, timeout=10)
        connection.row_factory = sqlite3.Row
        self._initialize_schema(connection)
        return connection

    @staticmethod
    def _initialize_schema(connection):
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS PERSONA (
                id_persona INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL UNIQUE,
                contrasena TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS USUARIO (
                id_persona INTEGER PRIMARY KEY,
                FOREIGN KEY (id_persona) REFERENCES PERSONA(id_persona) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS PASSWORD_RESET (
                token_hash TEXT PRIMARY KEY,
                id_persona INTEGER NOT NULL,
                expires_at REAL NOT NULL,
                used_at REAL,
                FOREIGN KEY (id_persona) REFERENCES PERSONA(id_persona) ON DELETE CASCADE
            );
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
        progress_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(PROGRESO_LECCION)"
            ).fetchall()
        }
        if "intentos" not in progress_columns:
            connection.execute(
                "ALTER TABLE PROGRESO_LECCION ADD COLUMN intentos INTEGER NOT NULL DEFAULT 0"
            )
        reset_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(PASSWORD_RESET)").fetchall()
        }
        if "intentos" not in reset_columns:
            connection.execute(
                "ALTER TABLE PASSWORD_RESET ADD COLUMN intentos INTEGER NOT NULL DEFAULT 0"
            )
        if "respuestas" not in progress_columns:
            connection.execute(
                "ALTER TABLE PROGRESO_LECCION ADD COLUMN respuestas TEXT"
            )

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
            (5, "Condicionales", "Toma decisiones con if, elif y else.", 1, 2, "condicionales"),
            (6, "Ciclos while", "Repite acciones mientras una condición sea verdadera.", 2, 2, "while"),
            (7, "Ciclos for", "Recorre secuencias con ciclos for.", 3, 2, "for"),
            (8, "Rompecabezas de control", "Combina decisiones y ciclos en un programa.", 4, 2, "control_rompecabezas"),
            (9, "Listas", "Crea, consulta y modifica listas.", 1, 3, "listas"),
            (10, "Tuplas y diccionarios", "Organiza datos con otras estructuras.", 2, 3, "estructuras"),
            (11, "Recorrido de estructuras", "Recorre colecciones con ciclos.", 3, 3, "recorrido"),
            (12, "Proyecto de estructuras", "Combina estructuras para resolver un ejercicio.", 4, 3, "proyecto_estructuras"),
            (13, "Funciones básicas", "Crea funciones reutilizables.", 1, 4, "funciones"),
            (14, "Parámetros y retorno", "Envía valores y devuelve resultados.", 2, 4, "parametros"),
            (15, "Alcance de variables", "Comprende variables locales y globales.", 3, 4, "alcance"),
            (16, "Proyecto final", "Construye un programa completo con funciones.", 4, 4, "proyecto_final"),
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
        lesson_quizzes = {
            1: [
                ("En nombre = 'Ana', ¿cuál es la variable?", "nombre", [("nombre", "nombre"), ("Ana", "Ana"), ("edad", "edad"), ("True", "True")]),
                ("¿Qué tipo de dato representa 20?", "int", [("int", "int"), ("str", "str"), ("float", "float"), ("bool", "bool")]),
                ("¿Qué valor representa el booleano verdadero?", "True", [("True", "True"), ("10", "10"), ("False", "False"), ("None", "None")]),
            ],
            2: [
                ("¿Qué valor guarda total = 3 + 4?", "7", [("7", "7"), ("34", "34"), ("12", "12"), ("1", "1")]),
                ("¿Qué devuelve 5 > 2?", "True", [("True", "True"), ("False", "False"), ("5", "5"), ("'True'", "'True'")]),
                ("¿Qué operador compara si dos valores son iguales?", "==", [("==", "=="), ("=", "="), ("!=", "!="), (">=", ">=")]),
            ],
            3: [
                ("¿Qué función muestra un mensaje en pantalla?", "print", [("print", "print()"), ("input", "input()"), ("return", "return"), ("len", "len()")]),
                ("¿Qué tipo devuelve input normalmente?", "str", [("str", "str"), ("int", "int"), ("float", "float"), ("bool", "bool")]),
                ("¿Qué convierte el texto de input a un entero?", "int", [("int", "int()"), ("print", "print()"), ("str", "str()"), ("float", "float()")]),
            ],
            4: [
                ("¿Cuánto vale 2 + 3 * 4?", "14", [("14", "14"), ("20", "20"), ("24", "24"), ("10", "10")]),
                ("¿Qué conversión permite guardar un precio decimal?", "float", [("float", "float()"), ("bool", "bool()"), ("int", "int()"), ("str", "str()")]),
                ("¿Qué muestra f'Hola {nombre}' si nombre es 'Ana'?", "Hola Ana", [("Hola Ana", "Hola Ana"), ("Hola {nombre}", "Hola {nombre}"), ("Ana", "Ana"), ("Hola nombre", "Hola nombre")]),
            ],
            5: [
                ("¿Qué palabra inicia una decisión en Python?", "if", [("if", "if"), ("for", "for"), ("elif", "elif"), ("else", "else")]),
                ("¿Qué palabra agrega otra condición después de if?", "elif", [("elif", "elif"), ("while", "while"), ("if", "if"), ("else", "else")]),
                ("¿Qué bloque cubre los casos restantes?", "else", [("else", "else"), ("return", "return"), ("elif", "elif"), ("if", "if")]),
            ],
            6: [
                ("¿Qué ciclo repite instrucciones mientras una condición sea verdadera?", "while", [("while", "while"), ("def", "def"), ("for", "for"), ("if", "if")]),
                ("¿Cómo disminuyes contador en una unidad?", "contador -= 1", [("contador -= 1", "contador -= 1"), ("contador =+ 1", "contador =+ 1"), ("contador += 1", "contador += 1"), ("contador = contador - 2", "contador = contador - 2")]),
                ("¿Qué evita que un ciclo cuente para siempre?", "actualizar", [("actualizar", "Actualizar la condición"), ("nada", "No cambiar nada"), ("repetir", "Repetir la misma condición"), ("borrar", "Borrar el ciclo")]),
            ],
            7: [
                ("¿Qué números recorre range(1, 4)?", "1, 2, 3", [("1, 2, 3", "1, 2, 3"), ("1, 2, 3, 4", "1, 2, 3, 4"), ("0, 1, 2", "0, 1, 2"), ("2, 3, 4", "2, 3, 4")]),
                ("¿Cómo recorres cada elemento de frutas?", "for fruta in frutas", [("for fruta in frutas", "for fruta in frutas:"), ("if fruta in frutas", "if fruta in frutas:"), ("while fruta in frutas", "while fruta in frutas:"), ("for frutas in fruta", "for frutas in fruta:")]),
                ("¿Qué devuelve range(3)?", "0, 1, 2", [("0, 1, 2", "0, 1, 2"), ("1, 2, 3", "1, 2, 3"), ("0, 1, 2, 3", "0, 1, 2, 3"), ("3", "3")]),
            ],
            8: [
                ("¿Qué expresión comprueba si numero es par?", "numero % 2 == 0", [("numero % 2 == 0", "numero % 2 == 0"), ("numero / 2 == 0", "numero / 2 == 0"), ("numero % 2 == 1", "numero % 2 == 1"), ("numero // 2 == 0", "numero // 2 == 0")]),
                ("¿Qué permite revisar una segunda regla solo si la primera se cumple?", "if_anidado", [("if_anidado", "Un if dentro de otro if"), ("print", "Un print dentro de otro print"), ("elif_anidado", "Un elif dentro de otro elif"), ("while_anidado", "Un while dentro de otro while")]),
                ("Si numero no es positivo, ¿qué bloque puede manejar el caso?", "else", [("else", "else"), ("elif", "elif sin condición"), ("if", "if"), ("finally", "finally")]),
            ],
            9: [
                ("¿Cómo escribes una lista con 1 y 2?", "[1, 2]", [("[1, 2]", "[1, 2]"), ("(1, 2)", "(1, 2)"), ("{1, 2}", "{1, 2}"), ("{'1': 2}", "{'1': 2}")]),
                ("¿Qué índice tiene el primer elemento de una lista?", "0", [("0", "0"), ("1", "1"), ("-1", "-1"), ("2", "2")]),
                ("¿Qué método agrega un valor al final de frutas?", "append", [("append", "append()"), ("remove", "remove()"), ("extend", "extend()"), ("insert", "insert()")]),
            ],
            10: [
                ("¿Qué estructura guarda datos asociados a claves?", "diccionario", [("diccionario", "Diccionario"), ("tupla", "Tupla"), ("lista", "Lista"), ("conjunto", "Conjunto")]),
                ("¿Cuál colección no se puede modificar después de crearla?", "tupla", [("tupla", "Tupla"), ("lista", "Lista"), ("diccionario", "Diccionario"), ("conjunto", "Conjunto")]),
                ("¿Cómo obtienes el nombre de estudiante = {'nombre': 'Ana'}?", "estudiante['nombre']", [("estudiante['nombre']", "estudiante['nombre']"), ("estudiante.nombre", "estudiante.nombre"), ("estudiante[0]", "estudiante[0]"), ("estudiante['edad']", "estudiante['edad']")]),
            ],
            11: [
                ("¿Qué ciclo procesa cada nota de una lista?", "for", [("for", "for"), ("elif", "elif"), ("while", "while"), ("if", "if")]),
                ("¿Qué devuelve estudiante.items()?", "pares", [("pares", "Pares de clave y valor"), ("claves", "Solo las claves"), ("valores", "Solo los valores"), ("lista", "Una lista con solo los valores")]),
                ("¿Qué genera range(1, 4)?", "1, 2, 3", [("1, 2, 3", "1, 2, 3"), ("0, 1, 2, 3", "0, 1, 2, 3"), ("1, 2, 3, 4", "1, 2, 3, 4"), ("0, 1, 2", "0, 1, 2")]),
            ],
            12: [
                ("¿Cómo calculas el promedio de notas?", "suma_dividida", [("suma_dividida", "sum(notas) / len(notas)"), ("multiplicar", "sum(notas) * len(notas)"), ("maximo", "max(notas)"), ("minimo", "min(notas)")]),
                ("¿Qué método agrega una nueva nota a la lista?", "append", [("append", "append()"), ("items", "items()"), ("extend", "extend()"), ("pop", "pop()")]),
                ("¿Qué estructura relaciona el nombre de cada estudiante con sus notas?", "diccionario", [("diccionario", "Diccionario"), ("booleano", "Booleano"), ("lista", "Lista"), ("conjunto", "Conjunto")]),
            ],
            13: [
                ("¿Qué palabra define una función?", "def", [("def", "def"), ("class", "class"), ("lambda", "lambda"), ("return", "return")]),
                ("¿Cómo ejecutas una función llamada saludar?", "saludar()", [("saludar()", "saludar()"), ("def saludar", "def saludar"), ("saludar", "saludar"), ("call saludar", "call saludar")]),
                ("¿Qué instrucción devuelve un valor desde una función?", "return", [("return", "return"), ("print", "print"), ("break", "break"), ("yield", "yield")]),
            ],
            14: [
                ("En def sumar(a, b), ¿qué son a y b?", "parametros", [("parametros", "Parámetros"), ("argumentos", "Argumentos"), ("variables_locales", "Variables locales"), ("resultados", "Resultados")]),
                ("¿Qué devuelve return a + b?", "resultado", [("resultado", "El resultado de la suma"), ("texto", "Siempre un texto"), ("funcion", "La función completa"), ("ninguno", "Ningún valor")]),
                ("¿Qué argumentos recibe sumar(3, 4)?", "3_y_4", [("3_y_4", "3 y 4"), ("a_y_b", "Las palabras a y b"), ("7", "7"), ("texto", "Los textos '3' y '4'")]),
            ],
            15: [
                ("¿Cómo se llama una variable creada dentro de una función?", "local", [("local", "Local"), ("global", "Global"), ("parametro", "Parámetro"), ("argumento", "Argumento")]),
                ("¿Qué permite enviar un dato a una función sin depender de una global?", "parametro", [("parametro", "Un parámetro"), ("variable_global", "Una variable global"), ("retorno", "Un retorno"), ("local", "Una variable local")]),
                ("¿Dónde existe normalmente una variable local?", "funcion", [("funcion", "Dentro de su función"), ("todo_programa", "En todo el programa"), ("siguiente_linea", "Solo en la siguiente línea"), ("llamada", "Solo durante la llamada")]),
            ],
            16: [
                ("¿Qué ayuda a reutilizar una parte del proyecto?", "funcion", [("funcion", "Una función"), ("comentario", "Un comentario"), ("variable", "Una variable"), ("bucle", "Un bucle")]),
                ("¿Qué instrucción entrega el cálculo al resto del programa?", "return", [("return", "return"), ("break", "break"), ("print", "print"), ("continue", "continue")]),
                ("¿Qué mejora la organización de un proyecto final?", "separar", [("separar", "Separar tareas en funciones pequeñas"), ("mezclar", "Escribir todo en un solo bloque"), ("variables", "Crear más variables"), ("comentarios", "Agregar comentarios a cada línea")]),
            ],
        }
        for lesson_id, questions in lesson_quizzes.items():
            for number, (question, answer, choices) in enumerate(questions, start=1):
                exercise_id = (
                    (lesson_id - 1) * 3 + number
                    if lesson_id <= 4
                    else lesson_id * 10 + number
                )
                options_json = json.dumps(
                    [
                        {"value": value, "label": label}
                        for value, label in choices
                    ],
                    ensure_ascii=False,
                )
                connection.execute(
                    """
                    INSERT INTO EJERCICIO_LECCION
                        (id_ejercicio, id_leccion, numero, pregunta, respuesta_correcta, opciones)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id_ejercicio) DO UPDATE SET
                        id_leccion = excluded.id_leccion,
                        numero = excluded.numero,
                        pregunta = excluded.pregunta,
                        respuesta_correcta = excluded.respuesta_correcta,
                        opciones = excluded.opciones
                    WHERE id_leccion IS NOT excluded.id_leccion
                        OR numero IS NOT excluded.numero
                        OR pregunta IS NOT excluded.pregunta
                        OR respuesta_correcta IS NOT excluded.respuesta_correcta
                        OR opciones IS NOT excluded.opciones
                    """,
                    (
                        exercise_id,
                        lesson_id,
                        number,
                        question,
                        answer,
                        options_json,
                    ),
                )
        connection.commit()
