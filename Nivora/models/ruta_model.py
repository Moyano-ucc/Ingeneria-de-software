class RutaModel:
    @staticmethod
    def obtener_rutas():
        # Módulos de aprendizaje definidos para Nivora[cite: 1]
        return [
            {
                "id": 1,
                "nombre": "Control de flujo",
                "completado": 0,
                "total": 2,
                "estado": "En progreso"
            },
            {
                "id": 2,
                "nombre": "Listas",
                "completado": 0,
                "total": 6,
                "estado": "Pendiente"
            },
            {
                "id": 3,
                "nombre": "Funciones",
                "completado": 0,
                "total": 5,
                "estado": "Pendiente"
            }
        ]