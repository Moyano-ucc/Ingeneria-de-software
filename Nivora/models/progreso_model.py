class ProgresoModel:

    @staticmethod
    def obtener_progreso(usuario_id=None, actividades=None):
        actividades = actividades or {}
        variables_completadas = sum(
            int(data.get('completada', False) if isinstance(data, dict) else data)
            for data in actividades.values()
        )
        general_completadas = variables_completadas

        return {
            "general": {
                "completadas": general_completadas,
                "total": 16,
                "porcentaje": round(general_completadas / 16 * 100)
            },

            "rutas": [
                {
                    "nombre": "Fundamentos de Python",
                    "completadas": variables_completadas,
                    "total": 4,
                    "porcentaje": round(variables_completadas / 4 * 100)
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