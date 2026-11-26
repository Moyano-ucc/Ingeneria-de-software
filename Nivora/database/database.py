import json
import os
import sqlite3
import threading

from database.contenido_inicial import (
    LECCIONES,
    OPCIONES_BASICAS,
    PREGUNTAS_BASICAS,
    QUIZZES_POR_LECCION,
    UNIDADES,
)


class DatabaseConnection:
    # The schema and course content are prepared once per database file and
    # process. Running it on every connection was slow and, with concurrent
    # first requests, two migrations could collide ("duplicate column name").
    initialized_paths = set()
    _init_lock = threading.Lock()

    def __init__(self, db_type="sqlite", config=None):
        self.db_type = db_type
        self.config = config or {}

    def path(self):
        """Absolute path of the SQLite file this connection uses."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.abspath(
            self.config.get("database_path")
            or os.environ.get(
                "NIVORA_DATABASE_PATH",
                os.path.join(base_dir, "database", "nivora.db"),
            )
        )

    def connect(self):
        if self.db_type != "sqlite":
            raise ValueError("Tipo de base de datos no soportado")

        database = self.path()
        parent_directory = os.path.dirname(os.path.abspath(database))
        os.makedirs(parent_directory, exist_ok=True)
        connection = sqlite3.connect(database, timeout=10)
        connection.row_factory = sqlite3.Row
        key = database
        if key not in self.initialized_paths:
            with self._init_lock:
                if key not in self.initialized_paths:
                    self._initialize_schema(connection)
                    self.initialized_paths.add(key)
        return connection

    @staticmethod
    def _add_column(connection, table, column, definition):
        """Add a column if it is missing (tolerates another process adding it)."""
        columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
        if column in columns:
            return
        try:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError as error:
            if "duplicate column" not in str(error):
                raise

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
            CREATE TABLE IF NOT EXISTS APUNTE (
                id_apunte INTEGER PRIMARY KEY AUTOINCREMENT,
                id_persona INTEGER NOT NULL,
                leccion_id TEXT NOT NULL,
                contenido TEXT NOT NULL,
                destacado INTEGER NOT NULL DEFAULT 0,
                creado REAL NOT NULL,
                actualizado REAL NOT NULL,
                FOREIGN KEY (id_persona) REFERENCES PERSONA(id_persona) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_apunte_persona_leccion
                ON APUNTE (id_persona, leccion_id);
            CREATE TABLE IF NOT EXISTS CERTIFICADO (
                id_persona INTEGER PRIMARY KEY,
                codigo TEXT NOT NULL UNIQUE,
                fecha_emision REAL NOT NULL,
                FOREIGN KEY (id_persona) REFERENCES PERSONA(id_persona) ON DELETE CASCADE
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
        DatabaseConnection._add_column(connection, "LECCION", "codigo", "TEXT")
        DatabaseConnection._add_column(
            connection, "PROGRESO_LECCION", "intentos", "INTEGER NOT NULL DEFAULT 0"
        )
        DatabaseConnection._add_column(connection, "PROGRESO_LECCION", "respuestas", "TEXT")
        DatabaseConnection._add_column(
            connection, "PASSWORD_RESET", "intentos", "INTEGER NOT NULL DEFAULT 0"
        )

        units = UNIDADES
        connection.executemany(
            "INSERT OR IGNORE INTO UNIDAD (id_unidad, nombre, descripcion, numero) VALUES (?, ?, ?, ?)",
            units,
        )

        lessons = LECCIONES
        # Lesson rows are course content, so they are refreshed when the text
        # changes (student progress lives in PROGRESO_LECCION and is untouched).
        connection.executemany(
            """
            INSERT INTO LECCION (id_leccion, titulo, contenido, numero, id_unidad, codigo)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id_leccion) DO UPDATE SET
                titulo = excluded.titulo,
                contenido = excluded.contenido
            WHERE titulo IS NOT excluded.titulo OR contenido IS NOT excluded.contenido
            """,
            lessons,
        )

        exercises = PREGUNTAS_BASICAS
        connection.executemany(
            "INSERT OR IGNORE INTO EJERCICIO (id_ejercicio, titulo, descripcion, dificultad, solucion_esperada, id_unidad) VALUES (?, ?, ?, 'basico', ?, 1)",
            [(number, title, question, answer) for number, title, question, answer in exercises],
        )

        options = OPCIONES_BASICAS
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
        lesson_quizzes = QUIZZES_POR_LECCION
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
