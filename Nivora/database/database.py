import sqlite3
import os


class DatabaseConnection:

    def __init__(self, db_type="sqlite", config=None):
        self.db_type = db_type
        self.config = config or {}

    def connect(self):
        if self.db_type == "sqlite":
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            database = self.config.get("database_path") or os.environ.get(
                "NIVORA_DATABASE_PATH",
                os.path.join(base_dir, "database", "nivora.db"),
            )

            conexion = sqlite3.connect(database, timeout=10)
            conexion.row_factory = sqlite3.Row

            return conexion

        raise ValueError("Tipo de base de datos no soportado")