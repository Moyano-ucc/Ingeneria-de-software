class ProgresoModel:

    @staticmethod
    def obtener_progreso(usuario_id=None, actividades=None):
        actividades = actividades or {}
        unit_one_ids = ("variables", "operadores", "entrada_salida", "repaso_fundamentos")
        unit_two_ids = ("condicionales", "while", "for", "control_rompecabezas")
        unit_three_ids = ("listas", "estructuras", "recorrido", "proyecto_estructuras")
        unit_four_ids = ("funciones", "parametros", "alcance", "proyecto_final")
        def count(ids):
            return sum(
                int(
                    data.get("completada", False)
                    if isinstance(data, dict)
                    else bool(data)
                )
                for data in (actividades.get(key, {}) for key in ids)
            )

        variables_completadas = count(unit_one_ids)
        unit_two_lessons_completed = count(unit_two_ids)
        puzzle_completed = int(
            actividades.get("unidad_02_puzzle", {}).get("completada", False)
            if isinstance(actividades.get("unidad_02_puzzle", {}), dict)
            else bool(actividades.get("unidad_02_puzzle", False))
        )
        unit_two_completed = min(unit_two_lessons_completed + puzzle_completed, 5)
        unit_three_completed = count(unit_three_ids)
        unit_four_completed = count(unit_four_ids)
        general_completadas = variables_completadas + unit_two_completed + unit_three_completed + unit_four_completed
        general_completadas = min(general_completadas, 17)
        total = 17

        return {
            "general": {
                "completadas": general_completadas,
                "total": total,
                "porcentaje": round(general_completadas / total * 100)
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
                    "total": 5,
                    "porcentaje": round(unit_two_completed / 5 * 100)
                },
                {
                    "nombre": "Listas y estructuras",
                    "completadas": unit_three_completed,
                    "total": 4,
                    "porcentaje": round(unit_three_completed / 4 * 100)
                },
                {
                    "nombre": "Funciones",
                    "completadas": unit_four_completed,
                    "total": 4,
                    "porcentaje": round(unit_four_completed / 4 * 100)
                }
            ]
        }