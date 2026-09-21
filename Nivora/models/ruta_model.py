class RutaModel:
    LESSONS = [
        {
            "id": "variables",
            "numero": 1,
            "titulo": "Variables y tipos de datos",
            "descripcion": "Guarda información y reconoce los tipos básicos de Python.",
            "answers": ["nombre", "int", "True"],
            "questions": [
                ("¿Qué nombre tiene el valor en nombre = \"Ana\"?", [("nombre", "nombre"), ("Ana", "Ana")]),
                ("¿Qué tipo de dato es 20?", [("int", "int"), ("str", "str")]),
                ("¿Cuál representa verdadero o falso?", [("True", "True"), ("10", "10")]),
            ],
        },
        {
            "id": "operadores",
            "numero": 2,
            "titulo": "Operadores y expresiones",
            "descripcion": "Realiza operaciones y compara valores.",
            "answers": ["7", "True", "=="],
            "questions": [
                ("¿Cuál es el resultado de 3 + 4?", [("7", "7"), ("12", "12")]),
                ("¿Qué devuelve 5 > 2?", [("True", "True"), ("False", "False")]),
                ("¿Qué operador compara igualdad?", [("==", "=="), ("=", "=")]),
            ],
        },
        {
            "id": "entrada_salida",
            "numero": 3,
            "titulo": "Entrada y salida de datos",
            "descripcion": "Muestra información y recibe datos del usuario.",
            "answers": ["print", "input", "texto"],
            "questions": [
                ("¿Qué función muestra texto?", [("print", "print"), ("input", "input")]),
                ("¿Qué función recibe datos?", [("input", "input"), ("print", "print")]),
                ("¿Qué devuelve input normalmente?", [("texto", "texto"), ("int", "int")]),
            ],
        },
        {
            "id": "repaso_fundamentos",
            "numero": 4,
            "titulo": "Repaso de fundamentos",
            "descripcion": "Comprueba lo aprendido en la primera ruta.",
            "answers": ["lista", "len", "append"],
            "questions": [
                ("¿Qué estructura guarda varios valores ordenados?", [("lista", "lista"), ("if", "if")]),
                ("¿Qué función obtiene la cantidad de elementos?", [("len", "len"), ("sum", "sum")]),
                ("¿Qué método agrega un elemento a una lista?", [("append", "append"), ("add", "add")]),
            ],
        },
    ]

    @staticmethod
    def obtener_rutas(actividades=None):
        actividades = actividades or {}
        completadas = sum(
            RutaModel._is_completed(actividades.get(lesson["id"], {}))
            for lesson in RutaModel.LESSONS
        )
        return [
            {
                "id": "01",
                "nombre": "Fundamentos de Python",
                "descripcion": "Aprende variables, tipos de datos, operadores y entrada y salida de datos.",
                "progreso": f"{completadas}/4",
                "estado": "Continuar"
            },
            {
                "id": "02",
                "nombre": "Control de flujo",
                "descripcion": "Aprende a utilizar condicionales y ciclos para controlar tus programas.",
                "progreso": "0/4",
                "estado": "Bloqueada"
            },
            {
                "id": "03",
                "nombre": "Listas y estructuras",
                "descripcion": "Aprende a trabajar con listas y otras estructuras para organizar información.",
                "progreso": "0/4",
                "estado": "Bloqueada"
            },
            {
                "id": "04",
                "nombre": "Funciones",
                "descripcion": "Crea funciones para organizar y reutilizar tu código.",
                "progreso": "0/4",
                "estado": "Bloqueada"
            }
        ]

    @staticmethod
    def obtener_leccion(lesson_id):
        return next((lesson for lesson in RutaModel.LESSONS if lesson["id"] == lesson_id), None)

    @staticmethod
    def _is_completed(activity):
        if isinstance(activity, dict):
            return bool(activity.get("completada"))
        return bool(activity)