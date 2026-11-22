import json

from fastapi import APIRouter, Request

from security import csrf_protected
from views.responses import redirect, render_template


practica_router = APIRouter(dependencies=csrf_protected)

EJERCICIOS = [
    {
        "id": "variables",
        "nivel": "Fácil",
        "pregunta": "Crea una variable llamada edad con el valor 20.",
        "respuesta": "edad = 20",
        "pista": "Usa el operador = para asignar el valor.",
    },
    {
        "id": "operadores",
        "nivel": "Fácil",
        "pregunta": "Guarda en total el resultado de sumar 3 y 4.",
        "respuesta": "total = 3 + 4",
        "pista": "Usa + para sumar y asigna el resultado a total.",
    },
    {
        "id": "entrada_salida",
        "nivel": "Fácil",
        "pregunta": "Pide el nombre de una persona con input.",
        "respuesta": 'nombre = input("Tu nombre: ")',
        "pista": "input devuelve el texto escrito por la persona.",
    },
    {
        "id": "repaso_fundamentos",
        "nivel": "Fácil",
        "pregunta": "Calcula e imprime el total de 5 unidades a 2 cada una.",
        "respuesta": "precio = 2\ncantidad = 5\nprint(precio * cantidad)",
        "pista": "Guarda precio y cantidad en variables y multiplica.",
    },
    {
        "id": "condicionales",
        "nivel": "Intermedio",
        "pregunta": "Ordena los bloques para que el programa clasifique la edad.",
        "pista": "El bloque else debe ir después del bloque if.",
        "tipo": "ordenar",
        "rompecabezas": {
            "bloques": [
                {"id": "adulto", "texto": "    print('Mayor')"},
                {"id": "menor", "texto": "    print('Menor')"},
                {"id": "sino", "texto": "else:"},
                {"id": "si", "texto": "if edad >= 18:"},
            ],
            "solucion": ["si", "adulto", "sino", "menor"],
        },
    },
    {
        "id": "while",
        "nivel": "Intermedio",
        "pregunta": "Completa la condición para que el contador llegue hasta 1.",
        "pista": "El ciclo continúa mientras el contador sea mayor que cero.",
        "tipo": "completar",
        "rompecabezas": {
            "partes": [
                "contador = 3\nwhile contador > ",
                ":\n    print(contador)\n    contador -= 1",
            ],
            "huecos": [
                {
                    "id": "limite",
                    "opciones": [
                        {"id": "cero", "texto": "0"},
                        {"id": "uno", "texto": "1"},
                        {"id": "tres", "texto": "3"},
                    ],
                },
            ],
            "solucion": {"limite": "cero"},
        },
    },
    {
        "id": "for",
        "nivel": "Intermedio",
        "pregunta": "Arma el ciclo que recorre los números del 1 al 3.",
        "pista": "La línea de print debe quedar dentro del ciclo for.",
        "tipo": "ordenar",
        "rompecabezas": {
            "bloques": [
                {"id": "salida", "texto": "    print(numero)"},
                {"id": "ciclo", "texto": "for numero in range(1, 4):"},
            ],
            "solucion": ["ciclo", "salida"],
        },
    },
    {
        "id": "control_rompecabezas",
        "nivel": "Intermedio",
        "pregunta": "Conecta cada condición con lo que comprueba.",
        "pista": "Fíjate en el operador usado en cada condición.",
        "tipo": "emparejar",
        "rompecabezas": {
            "izquierda": [
                {"id": "positivo", "texto": "numero > 0"},
                {"id": "par", "texto": "numero % 2 == 0"},
                {"id": "alternativa", "texto": "else"},
            ],
            "derecha": [
                {"id": "sin_condicion", "texto": "Ejecuta la alternativa si no se cumple el if."},
                {"id": "signo", "texto": "Comprueba si el número es positivo."},
                {"id": "residuo", "texto": "Comprueba si el número es par."},
            ],
            "solucion": {
                "positivo": "signo",
                "par": "residuo",
                "alternativa": "sin_condicion",
            },
        },
    },
    {
        "id": "listas",
        "nivel": "Intermedio",
        "pregunta": "Elige la ficha que agrega el 6 al final de la lista.",
        "pista": "Busca el método que añade un elemento al final.",
        "tipo": "completar",
        "rompecabezas": {
            "partes": ["numeros = [2, 4]\nnumeros.", "(6)"],
            "huecos": [
                {
                    "id": "metodo",
                    "opciones": [
                        {"id": "append", "texto": "append"},
                        {"id": "add", "texto": "add"},
                        {"id": "remove", "texto": "remove"},
                    ],
                },
            ],
            "solucion": {"metodo": "append"},
        },
    },
    {
        "id": "estructuras",
        "nivel": "Intermedio",
        "pregunta": "Empareja cada estructura con su característica.",
        "pista": "Los diccionarios guardan valores asociados a claves.",
        "tipo": "emparejar",
        "rompecabezas": {
            "izquierda": [
                {"id": "lista", "texto": "Lista"},
                {"id": "tupla", "texto": "Tupla"},
                {"id": "diccionario", "texto": "Diccionario"},
            ],
            "derecha": [
                {"id": "mutable", "texto": "Colección ordenada que se puede modificar."},
                {"id": "clave_valor", "texto": "Guarda valores asociados a claves."},
                {"id": "inmutable", "texto": "Colección ordenada que no se modifica."},
            ],
            "solucion": {
                "lista": "mutable",
                "tupla": "inmutable",
                "diccionario": "clave_valor",
            },
        },
    },
    {
        "id": "recorrido",
        "nivel": "Intermedio",
        "pregunta": "Ordena las piezas para recorrer e imprimir cada nota.",
        "pista": "Primero se declara el for y luego se ejecuta su bloque.",
        "tipo": "ordenar",
        "rompecabezas": {
            "bloques": [
                {"id": "imprimir", "texto": "    print(nota)"},
                {"id": "recorrer", "texto": "for nota in [8, 9, 10]:"},
            ],
            "solucion": ["recorrer", "imprimir"],
        },
    },
    {
        "id": "proyecto_estructuras",
        "nivel": "Avanzado",
        "pregunta": "Completa la operación que calcula el promedio de las notas.",
        "pista": "Divide la suma por la cantidad de elementos de la lista.",
        "tipo": "completar",
        "rompecabezas": {
            "partes": ["notas = [8, 9, 10]\npromedio = sum(notas) / ", "\nprint(promedio)"],
            "huecos": [
                {
                    "id": "cantidad",
                    "opciones": [
                        {"id": "len", "texto": "len(notas)"},
                        {"id": "sum", "texto": "sum(notas)"},
                        {"id": "primera", "texto": "notas[0]"},
                    ],
                },
            ],
            "solucion": {"cantidad": "len"},
        },
    },
    {
        "id": "funciones",
        "nivel": "Intermedio",
        "pregunta": "Ordena los bloques para crear una función que devuelva Hola.",
        "pista": "Una función empieza con def y su cuerpo lleva sangría.",
        "tipo": "ordenar",
        "rompecabezas": {
            "bloques": [
                {"id": "devolver", "texto": "    return 'Hola'"},
                {"id": "definir", "texto": "def saludo():"},
            ],
            "solucion": ["definir", "devolver"],
        },
    },
    {
        "id": "parametros",
        "nivel": "Intermedio",
        "pregunta": "Coloca la ficha que hace que sumar devuelva ambos valores juntos.",
        "pista": "La operación debe sumar a y b.",
        "tipo": "completar",
        "rompecabezas": {
            "partes": ["def sumar(a, b):\n    return a ", " b"],
            "huecos": [
                {
                    "id": "operador",
                    "opciones": [
                        {"id": "mas", "texto": "+"},
                        {"id": "menos", "texto": "-"},
                        {"id": "por", "texto": "*"},
                    ],
                },
            ],
            "solucion": {"operador": "mas"},
        },
    },
    {
        "id": "alcance",
        "nivel": "Avanzado",
        "pregunta": "Relaciona cada pieza de una función con su función.",
        "pista": "Los parámetros reciben datos y return entrega el resultado.",
        "tipo": "emparejar",
        "rompecabezas": {
            "izquierda": [
                {"id": "parametro", "texto": "precio"},
                {"id": "local", "texto": "total"},
                {"id": "return", "texto": "return total"},
            ],
            "derecha": [
                {"id": "entrega", "texto": "Devuelve un resultado al lugar donde se llamó."},
                {"id": "recibe", "texto": "Recibe un valor enviado a la función."},
                {"id": "interna", "texto": "Variable creada dentro de la función."},
            ],
            "solucion": {
                "parametro": "recibe",
                "local": "interna",
                "return": "entrega",
            },
        },
    },
    {
        "id": "proyecto_final",
        "nivel": "Avanzado",
        "pregunta": "Ordena las piezas para calcular e imprimir el promedio.",
        "pista": "Primero define la función, luego calcula el promedio y al final muéstralo.",
        "tipo": "ordenar",
        "rompecabezas": {
            "bloques": [
                {"id": "mostrar", "texto": "print(promedio)"},
                {"id": "calcular", "texto": "promedio = calcular_promedio([8, 9, 10])"},
                {"id": "retornar", "texto": "    return sum(notas) / len(notas)"},
                {"id": "definir", "texto": "def calcular_promedio(notas):"},
            ],
            "solucion": ["definir", "retornar", "calcular", "mostrar"],
        },
    },
]


def _validate_puzzle_answer(exercise, raw_answer):
    puzzle = exercise["rompecabezas"]
    try:
        answer = json.loads(raw_answer)
    except (TypeError, json.JSONDecodeError):
        answer = None

    if exercise["tipo"] == "ordenar":
        valid_ids = {block["id"] for block in puzzle["bloques"]}
        valid_structure = (
            isinstance(answer, list)
            and len(answer) == len(valid_ids)
            and all(isinstance(item, str) and item in valid_ids for item in answer)
        )
        normalized = (
            answer[:len(valid_ids)]
            if isinstance(answer, list)
            else []
        )
        correct = (
            valid_structure
            and normalized == puzzle["solucion"]
            and len(set(normalized)) == len(normalized)
        )
        return normalized, correct

    if exercise["tipo"] == "completar":
        options = {
            gap["id"]: {option["id"] for option in gap["opciones"]}
            for gap in puzzle["huecos"]
        }
        normalized = (
            {
                key: value
                for key, value in answer.items()
                if key in options
                and isinstance(value, str)
                and value in options[key]
            }
            if isinstance(answer, dict)
            else {}
        )
        correct = (
            isinstance(answer, dict)
            and len(answer) == len(normalized)
            and normalized == puzzle["solucion"]
            and len(set(normalized.values())) == len(normalized)
        )
        return normalized, correct

    valid_left = {item["id"] for item in puzzle["izquierda"]}
    valid_right = {item["id"] for item in puzzle["derecha"]}
    normalized = (
        {
            key: value
            for key, value in answer.items()
            if key in valid_left
            and isinstance(value, str)
            and value in valid_right
        }
        if isinstance(answer, dict)
        else {}
    )
    correct = (
        normalized == puzzle["solucion"]
        and len(answer) == len(normalized)
        and len(set(normalized.values())) == len(normalized)
        if isinstance(answer, dict)
        else False
    )
    return normalized, correct


@practica_router.api_route(
    "/practica",
    methods=["GET", "POST"],
    name="practica.mostrar_practica",
)
async def mostrar_practica(request: Request):
    if "usuario" not in request.session:
        return redirect(request.url_for("auth.login"))

    form = await request.form() if request.method == "POST" else {}
    ejercicio_id = (
        form.get("ejercicio")
        if request.method == "POST"
        else request.query_params.get("ejercicio", "variables")
    )
    ejercicio = next(
        (item for item in EJERCICIOS if item["id"] == ejercicio_id),
        EJERCICIOS[0],
    )
    if request.method == "POST":
        if "tipo" in ejercicio:
            answer, correct = _validate_puzzle_answer(
                ejercicio,
                form.get("respuesta", ""),
            )
            request.session["practice_result"] = {
                "ejercicio_id": ejercicio_id,
                "correcto": correct,
                "respuesta": answer,
            }
        else:
            codigo = str(form.get("codigo", "")).strip()
            request.session["practice_result"] = {
                "ejercicio_id": ejercicio_id,
                "correcto": " ".join(codigo.lower().split())
                == " ".join(ejercicio["respuesta"].lower().split()),
                "codigo": codigo,
            }
        destination = request.url_for("practica.mostrar_practica").include_query_params(
            ejercicio=ejercicio_id
        )
        return redirect(
            destination,
            status_code=303,
        )

    feedback = request.session.pop("practice_result", None)
    resultado = (
        feedback
        if isinstance(feedback, dict)
        and feedback.get("ejercicio_id") == ejercicio_id
        else None
    )

    return render_template(
        request,
        "practica.html",
        ejercicios=EJERCICIOS,
        ejercicio=ejercicio,
        resultado=resultado,
    )
