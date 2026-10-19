
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

        os.makedirs(os.path.dirname(os.path.abspath(database)), exist_ok=True)

        connection = sqlite3.connect(database, timeout=10)
        connection.row_factory = sqlite3.Row
        self._initialize_schema(connection)

        return connection

    @staticmethod
    def _initialize_schema(connection):
        connection.execute("PRAGMA foreign_keys = ON")

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
                FOREIGN KEY (id_persona)
                    REFERENCES PERSONA(id_persona) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS PASSWORD_RESET (
                token_hash TEXT PRIMARY KEY,
                id_persona INTEGER NOT NULL,
                expires_at REAL NOT NULL,
                used_at REAL,
                FOREIGN KEY (id_persona)
                    REFERENCES PERSONA(id_persona) ON DELETE CASCADE
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
            for row in connection.execute(
                "PRAGMA table_info(LECCION)"
            ).fetchall()
        }

        if "codigo" not in lesson_columns:
            connection.execute(
                "ALTER TABLE LECCION ADD COLUMN codigo TEXT"
            )

        # UNIDADES
        units = [
            (
                1,
                "Fundamentos de Python",
                "Aprende variables, tipos de datos, operadores, "
                "entrada y salida de datos y conversión de valores.",
                1,
            ),
            (
                2,
                "Control de flujo",
                "Aprende condicionales, operadores lógicos y ciclos "
                "para controlar tus programas.",
                2,
            ),
            (
                3,
                "Listas y estructuras",
                "Aprende a trabajar con listas y otras estructuras "
                "para organizar información.",
                3,
            ),
            (
                4,
                "Funciones",
                "Crea funciones para organizar y reutilizar tu código.",
                4,
            ),
        ]

        connection.executemany(
            """
            INSERT OR IGNORE INTO UNIDAD
                (id_unidad, nombre, descripcion, numero)
            VALUES (?, ?, ?, ?)
            """,
            units,
        )

        # LECCIONES
        # Se conservan los identificadores originales del 1 al 4.
        lessons = [
            (
                1,
                "Variables y tipos de datos",
                "Aprende a guardar información en variables "
                "y reconocer los tipos de datos de Python.",
                1,
                1,
                "variables",
            ),
            (
                2,
                "Operadores y expresiones",
                "Realiza operaciones aritméticas, compara valores "
                "y construye expresiones.",
                2,
                1,
                "operadores",
            ),
            (
                3,
                "Entrada y salida de datos",
                "Aprende a recibir datos con input y mostrar "
                "resultados con print.",
                3,
                1,
                "entrada_salida",
            ),
            (
                4,
                "Repaso de fundamentos",
                "Combina variables, operadores y entrada y salida "
                "de datos en un ejercicio de repaso.",
                4,
                1,
                "repaso_fundamentos",
            ),
            (
                5,
                "Conversión de datos",
                "Convierte textos en números, distingue int y float "
                "y evita errores al realizar operaciones.",
                5,
                1,
                "conversion_datos",
            ),
            (
                6,
                "Cadenas de texto",
                "Trabaja con textos, concatenación, métodos "
                "y formato de cadenas.",
                6,
                1,
                "cadenas_texto",
            ),
            (
                7,
                "Condicionales",
                "Utiliza if, elif y else para ejecutar instrucciones "
                "según una condición.",
                1,
                2,
                "condicionales",
            ),
            (
                8,
                "Operadores lógicos",
                "Combina condiciones con and, or y not "
                "para tomar decisiones.",
                2,
                2,
                "operadores_logicos",
            ),
            (
                9,
                "Ciclo for",
                "Repite instrucciones y recorre secuencias "
                "utilizando el ciclo for y range.",
                3,
                2,
                "ciclo_for",
            ),
            (
                10,
                "Ciclo while",
                "Repite instrucciones mientras una condición "
                "sea verdadera y aprende a controlar el ciclo.",
                4,
                2,
                "ciclo_while",
            ),
        ]

        connection.executemany(
            """
            INSERT OR IGNORE INTO LECCION
                (id_leccion, titulo, contenido, numero, id_unidad, codigo)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            lessons,
        )

        # PREGUNTAS Y EJERCICIOS
        # Formato:
        # (id, titulo, pregunta, respuesta, id_unidad)
        exercises = [
            # Unidad 1 - Variables
            (
                1, "Pregunta 1",
                '¿Qué nombre tiene el valor en nombre = "Ana"?',
                "nombre", 1,
            ),
            (
                2, "Pregunta 2",
                "¿Qué tipo de dato es 20?",
                "int", 1,
            ),
            (
                3, "Pregunta 3",
                "¿Cuál representa verdadero o falso?",
                "True", 1,
            ),

            # Unidad 1 - Operadores
            (
                4, "Pregunta 1",
                "¿Cuál es el resultado de 3 + 4?",
                "7", 1,
            ),
            (
                5, "Pregunta 2",
                "¿Qué devuelve 5 > 2?",
                "True", 1,
            ),
            (
                6, "Pregunta 3",
                "¿Qué operador compara igualdad?",
                "==", 1,
            ),

            # Unidad 1 - Entrada y salida
            (
                7, "Pregunta 1",
                "¿Qué función muestra texto?",
                "print", 1,
            ),
            (
                8, "Pregunta 2",
                "¿Qué función recibe datos?",
                "input", 1,
            ),
            (
                9, "Pregunta 3",
                "¿Qué devuelve input normalmente?",
                "texto", 1,
            ),

            # Unidad 1 - Repaso
            (
                10, "Pregunta 1",
                "¿Qué estructura guarda varios valores ordenados?",
                "lista", 1,
            ),
            (
                11, "Pregunta 2",
                "¿Qué función obtiene la cantidad de elementos?",
                "len", 1,
            ),
            (
                12, "Pregunta 3",
                "¿Qué método agrega un elemento a una lista?",
                "append", 1,
            ),

            # Unidad 1 - Conversión de datos
            (
                13, "Pregunta 1",
                "¿Qué función convierte un texto entero en número?",
                "int", 1,
            ),
            (
                14, "Pregunta 2",
                "¿Qué tipo de dato representa 3.5?",
                "float", 1,
            ),
            (
                15, "Pregunta 3",
                "¿Qué función convierte un número en texto?",
                "str", 1,
            ),

            # Unidad 1 - Cadenas de texto
            (
                16, "Pregunta 1",
                "¿Qué tipo de dato representa 'Hola'?",
                "str", 1,
            ),
            (
                17, "Pregunta 2",
                "¿Qué método convierte un texto a minúsculas?",
                "lower", 1,
            ),
            (
                18, "Pregunta 3",
                "¿Qué carácter permite escribir un salto de línea?",
                "\\n", 1,
            ),

            # Unidad 2 - Condicionales
            (
                19, "Pregunta 1",
                "¿Qué palabra inicia una condición en Python?",
                "if", 2,
            ),
            (
                20, "Pregunta 2",
                "¿Qué palabra permite comprobar otra condición?",
                "elif", 2,
            ),
            (
                21, "Pregunta 3",
                "¿Qué palabra permite ejecutar el caso contrario?",
                "else", 2,
            ),

            # Unidad 2 - Operadores lógicos
            (
                22, "Pregunta 1",
                "¿Qué operador lógico exige que ambas condiciones sean verdaderas?",
                "and", 2,
            ),
            (
                23, "Pregunta 2",
                "¿Qué operador lógico acepta que una condición sea verdadera?",
                "or", 2,
            ),
            (
                24, "Pregunta 3",
                "¿Qué operador invierte un valor booleano?",
                "not", 2,
            ),

            # Unidad 2 - Ciclo for
            (
                25, "Pregunta 1",
                "¿Qué ciclo permite recorrer una secuencia?",
                "for", 2,
            ),
            (
                26, "Pregunta 2",
                "¿Qué función genera una secuencia de números?",
                "range", 2,
            ),
            (
                27, "Pregunta 3",
                "¿Cuántas veces se ejecuta for i in range(3)?",
                "3", 2,
            ),

            # Unidad 2 - Ciclo while
            (
                28, "Pregunta 1",
                "¿Qué ciclo se repite mientras una condición sea verdadera?",
                "while", 2,
            ),
            (
                29, "Pregunta 2",
                "¿Qué instrucción termina un ciclo inmediatamente?",
                "break", 2,
            ),
            (
                30, "Pregunta 3",
                "¿Qué puede pasar si la condición nunca se vuelve falsa?",
                "infinito", 2,
            ),
        ]

        connection.executemany(
            """
            INSERT OR IGNORE INTO EJERCICIO
                (
                    id_ejercicio,
                    titulo,
                    descripcion,
                    dificultad,
                    solucion_esperada,
                    id_unidad
                )
            VALUES (?, ?, ?, 'basico', ?, ?)
            """,
            [
                (
                    exercise_id,
                    title,
                    question,
                    answer,
                    unit_id,
                )
                for exercise_id, title, question, answer, unit_id
                in exercises
            ],
        )

        # OPCIONES DE LOS QUIZZES
        # Formato:
        # (id_ejercicio, id_leccion, numero, respuesta, opciones_json)
        options = [
            # Variables - lección 1
            (
                1, 1, 1, "nombre",
                '[{"value":"nombre","label":"nombre"},'
                '{"value":"Ana","label":"Ana"}]',
            ),
            (
                2, 1, 2, "int",
                '[{"value":"int","label":"int"},'
                '{"value":"str","label":"str"}]',
            ),
            (
                3, 1, 3, "True",
                '[{"value":"True","label":"True"},'
                '{"value":"10","label":"10"}]',
            ),

            # Operadores - lección 2
            (
                4, 2, 1, "7",
                '[{"value":"7","label":"7"},'
                '{"value":"12","label":"12"}]',
            ),
            (
                5, 2, 2, "True",
                '[{"value":"True","label":"True"},'
                '{"value":"False","label":"False"}]',
            ),
            (
                6, 2, 3, "==",
                '[{"value":"==","label":"=="},'
                '{"value":"=","label":"="}]',
            ),

            # Entrada y salida - lección 3
            (
                7, 3, 1, "print",
                '[{"value":"print","label":"print"},'
                '{"value":"input","label":"input"}]',
            ),
            (
                8, 3, 2, "input",
                '[{"value":"input","label":"input"},'
                '{"value":"print","label":"print"}]',
            ),
            (
                9, 3, 3, "texto",
                '[{"value":"texto","label":"texto"},'
                '{"value":"int","label":"int"}]',
            ),

            # Repaso - lección 4
            (
                10, 4, 1, "lista",
                '[{"value":"lista","label":"lista"},'
                '{"value":"if","label":"if"}]',
            ),
            (
                11, 4, 2, "len",
                '[{"value":"len","label":"len"},'
                '{"value":"sum","label":"sum"}]',
            ),
            (
                12, 4, 3, "append",
                '[{"value":"append","label":"append"},'
                '{"value":"add","label":"add"}]',
            ),

            # Conversión de datos - lección 5
            (
                13, 5, 1, "int",
                '[{"value":"int","label":"int"},'
                '{"value":"input","label":"input"}]',
            ),
            (
                14, 5, 2, "float",
                '[{"value":"float","label":"float"},'
                '{"value":"bool","label":"bool"}]',
            ),
            (
                15, 5, 3, "str",
                '[{"value":"str","label":"str"},'
                '{"value":"int","label":"int"}]',
            ),

            # Cadenas de texto - lección 6
            (
                16, 6, 1, "str",
                '[{"value":"str","label":"str"},'
                '{"value":"float","label":"float"}]',
            ),
            (
                17, 6, 2, "lower",
                '[{"value":"lower","label":"lower"},'
                '{"value":"upper","label":"upper"}]',
            ),
            (
                18, 6, 3, "\\n",
                '[{"value":"\\\\n","label":"\\\\n"},'
                '{"value":"\\\\t","label":"\\\\t"}]',
            ),

            # Condicionales - lección 7
            (
                19, 7, 1, "if",
                '[{"value":"if","label":"if"},'
                '{"value":"for","label":"for"}]',
            ),
            (
                20, 7, 2, "elif",
                '[{"value":"elif","label":"elif"},'
                '{"value":"print","label":"print"}]',
            ),
            (
                21, 7, 3, "else",
                '[{"value":"else","label":"else"},'
                '{"value":"input","label":"input"}]',
            ),

            # Operadores lógicos - lección 8
            (
                22, 8, 1, "and",
                '[{"value":"and","label":"and"},'
                '{"value":"or","label":"or"}]',
            ),
            (
                23, 8, 2, "or",
                '[{"value":"or","label":"or"},'
                '{"value":"not","label":"not"}]',
            ),
            (
                24, 8, 3, "not",
                '[{"value":"not","label":"not"},'
                '{"value":"and","label":"and"}]',
            ),

            # Ciclo for - lección 9
            (
                25, 9, 1, "for",
                '[{"value":"for","label":"for"},'
                '{"value":"if","label":"if"}]',
            ),
            (
                26, 9, 2, "range",
                '[{"value":"range","label":"range"},'
                '{"value":"len","label":"len"}]',
            ),
            (
                27, 9, 3, "3",
                '[{"value":"3","label":"3"},'
                '{"value":"2","label":"2"}]',
            ),

            # Ciclo while - lección 10
            (
                28, 10, 1, "while",
                '[{"value":"while","label":"while"},'
                '{"value":"for","label":"for"}]',
            ),
            (
                29, 10, 2, "break",
                '[{"value":"break","label":"break"},'
                '{"value":"continue","label":"continue"}]',
            ),
            (
                30, 10, 3, "infinito",
                '[{"value":"infinito","label":"infinito"},'
                '{"value":"una vez","label":"una vez"}]',
            ),
        ]

        connection.executemany(
            """
            INSERT OR IGNORE INTO EJERCICIO_LECCION
                (
                    id_ejercicio,
                    id_leccion,
                    numero,
                    pregunta,
                    respuesta_correcta,
                    opciones
                )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    exercise_id,
                    lesson_id,
                    number,
                    next(
                        item[2]
                        for item in exercises
                        if item[0] == exercise_id
                    ),
                    correct_answer,
                    option_data,
                )
                for (
                    exercise_id,
                    lesson_id,
                    number,
                    correct_answer,
                    option_data,
                ) in options
            ],
        )

        connection.commit()
