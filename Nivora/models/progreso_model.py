class ProgresoModel:

    @staticmethod
    def obtener_progreso(usuario_id=None, actividades=None):
        actividades = actividades or {}
        unit_one_activities = {
            key: value for key, value in actividades.items()
            if key != "unidad_02_puzzle"
        }
        variables_completadas = sum(
            int(data.get('completada', False) if isinstance(data, dict) else data)
            for data in unit_one_activities.values()
        )
        unit_two_completed = int(
            actividades.get("unidad_02_puzzle", {}).get("completada", False)
            if isinstance(actividades.get("unidad_02_puzzle", {}), dict)
            else bool(actividades.get("unidad_02_puzzle", False))
        )
        general_completadas = variables_completadas + unit_two_completed

        return {
            "general": {
                "completadas": general_completadas,
                "total": 13,
                "porcentaje": round(general_completadas / 13 * 100)
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
                    "completadas": unit_two_completed,
                    "total": 1,
                    "porcentaje": unit_two_completed * 100
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