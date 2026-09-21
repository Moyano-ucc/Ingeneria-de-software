import sqlite3
import os


class AdaptativeConnection:

    _instance = None

    def __new__(cls, db_type="sqlite", config=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db_type = db_type
            cls._instance.config = config or {}

        return cls._instance

    def connect(self):
        if self.db_type == "sqlite":
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            database = os.path.join(base_dir, "database", "nivora.db")

            conexion = sqlite3.connect(database)
            conexion.row_factory = sqlite3.Row

            return conexion

        raise ValueError("Tipo de base de datos no soportado")