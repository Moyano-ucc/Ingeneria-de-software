class ProgresoModel:

    @staticmethod
    def obtener_progreso():

        return {
            "general": {
                "completadas": 0,
                "total": 16,
                "porcentaje": 0
            },

            "rutas": [
                {
                    "nombre": "Fundamentos de Python",
                    "completadas": 0,
                    "total": 4,
                    "porcentaje": 0
                },
                {
                    "nombre": "Control de flujo",
                    "completadas": 0,
                    "total": 4,
                    "porcentaje": 0
                },
                {
                    "nombre": "Listas y estructuras",
                    "completadas": 0,
                    "total": 4,
                    "porcentaje": 0
                },
                {
                    "nombre": "Funciones",
                    "completadas": 0,
                    "total": 4,
                    "porcentaje": 0
                }
            ]
        }