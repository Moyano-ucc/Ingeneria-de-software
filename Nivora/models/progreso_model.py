from models.ruta_model import RutaModel


class ProgresoModel:
    """Overall and per-unit progress, derived from the lessons in the database.

    Totals come from the real content, so adding or removing a lesson keeps
    the percentages and the course completion consistent.
    """

    @staticmethod
    def _percentage(completed, total):
        return round(completed / total * 100) if total else 0

    @classmethod
    def obtener_progreso(cls, usuario_id=None, actividades=None):
        rutas = RutaModel.obtener_rutas(actividades or {})
        completadas = sum(ruta["completadas"] for ruta in rutas)
        total = sum(ruta["total"] for ruta in rutas)
        return {
            "general": {
                "completadas": completadas,
                "total": total,
                "porcentaje": cls._percentage(completadas, total),
            },
            "rutas": [
                {
                    "nombre": ruta["nombre"],
                    "completadas": ruta["completadas"],
                    "total": ruta["total"],
                    "porcentaje": cls._percentage(ruta["completadas"], ruta["total"]),
                }
                for ruta in rutas
            ],
            "curso_completado": total > 0 and completadas == total,
        }
