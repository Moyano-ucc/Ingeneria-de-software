class RutaModel:
    @staticmethod
    def obtener_rutas():
        # Módulos y formato de progreso estipulados en RF-03 de Nivora
        return [
            {
                "id": 1,
                "nombre": "Control de flujo",
                "completado": 1,
                "total": 6,
                "progreso_texto": "1/6"
            },
            {
                "id": 2,
                "nombre": "Listas",
                "completado": 0,
                "total": 2,
                "progreso_texto": "0/2"
            },
            {
                "id": 3,
                "nombre": "Funciones",
                "completado": 0,
                "total": 5,
                "progreso_texto": "0/5"
            }
        ]