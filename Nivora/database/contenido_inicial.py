"""Initial course content: units, lessons and quiz questions.

``database.py`` inserts or refreshes these rows when the application starts.
Keeping the data here separates *what* the course contains from *how* the
database is connected and prepared (single responsibility).
"""

UNIDADES = [
    (1, "Fundamentos de Python", "Aprende variables, tipos de datos, operadores y entrada y salida de datos.", 1),
    (2, "Control de flujo", "Aprende a utilizar condicionales y ciclos para controlar tus programas.", 2),
    (3, "Listas y estructuras", "Aprende a trabajar con listas y otras estructuras para organizar información.", 3),
    (4, "Funciones", "Crea funciones para organizar y reutilizar tu código.", 4),
]

LECCIONES = [
    (1, "Variables y tipos de datos", "Guarda información y reconoce los tipos básicos de Python.", 1, 1, "variables"),
    (2, "Operadores y expresiones", "Realiza operaciones y compara valores.", 2, 1, "operadores"),
    (3, "Entrada y salida de datos", "Muestra información y recibe datos del usuario.", 3, 1, "entrada_salida"),
    (4, "Repaso de fundamentos", "Comprueba lo aprendido en la primera ruta.", 4, 1, "repaso_fundamentos"),
    (5, "Condicionales", "Toma decisiones con if, elif y else.", 1, 2, "condicionales"),
    (6, "Ciclos while", "Repite acciones mientras una condición sea verdadera.", 2, 2, "while"),
    (7, "Ciclos for", "Recorre secuencias con ciclos for.", 3, 2, "for"),
    (8, "Rompecabezas de control", "Combina decisiones y ciclos en un programa.", 4, 2, "control_rompecabezas"),
    (9, "Listas", "Crea, consulta y modifica listas.", 1, 3, "listas"),
    (10, "Tuplas y diccionarios", "Organiza datos con otras estructuras.", 2, 3, "estructuras"),
    (11, "Recorrido de estructuras", "Recorre colecciones con ciclos.", 3, 3, "recorrido"),
    (12, "Proyecto de estructuras", "Combina estructuras para resolver un ejercicio.", 4, 3, "proyecto_estructuras"),
    (13, "Funciones básicas", "Crea funciones reutilizables.", 1, 4, "funciones"),
    (14, "Parámetros y retorno", "Envía valores y devuelve resultados.", 2, 4, "parametros"),
    (15, "Alcance de variables", "Comprende variables locales y globales.", 3, 4, "alcance"),
    (16, "Proyecto final", "Construye un boletín de calificaciones que combina todo el curso.", 4, 4, "proyecto_final"),
]

PREGUNTAS_BASICAS = [
    (1, "Pregunta 1", "¿Qué nombre tiene el valor en nombre = \"Ana\"?", "nombre"),
    (2, "Pregunta 2", "¿Qué tipo de dato es 20?", "int"),
    (3, "Pregunta 3", "¿Cuál representa verdadero o falso?", "True"),
    (4, "Pregunta 1", "¿Cuál es el resultado de 3 + 4?", "7"),
    (5, "Pregunta 2", "¿Qué devuelve 5 > 2?", "True"),
    (6, "Pregunta 3", "¿Qué operador compara igualdad?", "=="),
    (7, "Pregunta 1", "¿Qué función muestra texto?", "print"),
    (8, "Pregunta 2", "¿Qué función recibe datos?", "input"),
    (9, "Pregunta 3", "¿Qué devuelve input normalmente?", "texto"),
    (10, "Pregunta 1", "¿Qué estructura guarda varios valores ordenados?", "lista"),
    (11, "Pregunta 2", "¿Qué función obtiene la cantidad de elementos?", "len"),
    (12, "Pregunta 3", "¿Qué método agrega un elemento a una lista?", "append"),
]

OPCIONES_BASICAS = [
    (1, 1, 1, "nombre", '[{"value": "nombre", "label": "nombre"}, {"value": "Ana", "label": "Ana"}]'),
    (2, 1, 2, "int", '[{"value": "int", "label": "int"}, {"value": "str", "label": "str"}]'),
    (3, 1, 3, "True", '[{"value": "True", "label": "True"}, {"value": "10", "label": "10"}]'),
    (4, 2, 1, "7", '[{"value": "7", "label": "7"}, {"value": "12", "label": "12"}]'),
    (5, 2, 2, "True", '[{"value": "True", "label": "True"}, {"value": "False", "label": "False"}]'),
    (6, 2, 3, "==", '[{"value": "==", "label": "=="}, {"value": "=", "label": "="}]'),
    (7, 3, 1, "print", '[{"value": "print", "label": "print"}, {"value": "input", "label": "input"}]'),
    (8, 3, 2, "input", '[{"value": "input", "label": "input"}, {"value": "print", "label": "print"}]'),
    (9, 3, 3, "texto", '[{"value": "texto", "label": "texto"}, {"value": "int", "label": "int"}]'),
    (10, 4, 1, "lista", '[{"value": "lista", "label": "lista"}, {"value": "if", "label": "if"}]'),
    (11, 4, 2, "len", '[{"value": "len", "label": "len"}, {"value": "sum", "label": "sum"}]'),
    (12, 4, 3, "append", '[{"value": "append", "label": "append"}, {"value": "add", "label": "add"}]'),
]

QUIZZES_POR_LECCION = {
    1: [
        ("En nombre = 'Ana', ¿cuál es la variable?", "nombre", [("nombre", "nombre"), ("Ana", "Ana"), ("edad", "edad"), ("True", "True")]),
        ("¿Qué tipo de dato representa 20?", "int", [("int", "int"), ("str", "str"), ("float", "float"), ("bool", "bool")]),
        ("¿Qué valor representa el booleano verdadero?", "True", [("True", "True"), ("10", "10"), ("False", "False"), ("None", "None")]),
    ],
    2: [
        ("¿Qué valor guarda total = 3 + 4?", "7", [("7", "7"), ("34", "34"), ("12", "12"), ("1", "1")]),
        ("¿Qué devuelve 5 > 2?", "True", [("True", "True"), ("False", "False"), ("5", "5"), ("'True'", "'True'")]),
        ("¿Qué operador compara si dos valores son iguales?", "==", [("==", "=="), ("=", "="), ("!=", "!="), (">=", ">=")]),
    ],
    3: [
        ("¿Qué función muestra un mensaje en pantalla?", "print", [("print", "print()"), ("input", "input()"), ("return", "return"), ("len", "len()")]),
        ("¿Qué tipo devuelve input normalmente?", "str", [("str", "str"), ("int", "int"), ("float", "float"), ("bool", "bool")]),
        ("¿Qué convierte el texto de input a un entero?", "int", [("int", "int()"), ("print", "print()"), ("str", "str()"), ("float", "float()")]),
    ],
    4: [
        ("¿Cuánto vale 2 + 3 * 4?", "14", [("14", "14"), ("20", "20"), ("24", "24"), ("10", "10")]),
        ("¿Qué conversión permite guardar un precio decimal?", "float", [("float", "float()"), ("bool", "bool()"), ("int", "int()"), ("str", "str()")]),
        ("¿Qué muestra f'Hola {nombre}' si nombre es 'Ana'?", "Hola Ana", [("Hola Ana", "Hola Ana"), ("Hola {nombre}", "Hola {nombre}"), ("Ana", "Ana"), ("Hola nombre", "Hola nombre")]),
    ],
    5: [
        ("¿Qué palabra inicia una decisión en Python?", "if", [("if", "if"), ("for", "for"), ("elif", "elif"), ("else", "else")]),
        ("¿Qué palabra agrega otra condición después de if?", "elif", [("elif", "elif"), ("while", "while"), ("if", "if"), ("else", "else")]),
        ("¿Qué bloque cubre los casos restantes?", "else", [("else", "else"), ("return", "return"), ("elif", "elif"), ("if", "if")]),
    ],
    6: [
        ("¿Qué ciclo repite instrucciones mientras una condición sea verdadera?", "while", [("while", "while"), ("def", "def"), ("for", "for"), ("if", "if")]),
        ("¿Cómo disminuyes contador en una unidad?", "contador -= 1", [("contador -= 1", "contador -= 1"), ("contador =+ 1", "contador =+ 1"), ("contador += 1", "contador += 1"), ("contador = contador - 2", "contador = contador - 2")]),
        ("¿Qué evita que un ciclo cuente para siempre?", "actualizar", [("actualizar", "Actualizar la condición"), ("nada", "No cambiar nada"), ("repetir", "Repetir la misma condición"), ("borrar", "Borrar el ciclo")]),
    ],
    7: [
        ("¿Qué números recorre range(1, 4)?", "1, 2, 3", [("1, 2, 3", "1, 2, 3"), ("1, 2, 3, 4", "1, 2, 3, 4"), ("0, 1, 2", "0, 1, 2"), ("2, 3, 4", "2, 3, 4")]),
        ("¿Cómo recorres cada elemento de frutas?", "for fruta in frutas", [("for fruta in frutas", "for fruta in frutas:"), ("if fruta in frutas", "if fruta in frutas:"), ("while fruta in frutas", "while fruta in frutas:"), ("for frutas in fruta", "for frutas in fruta:")]),
        ("¿Qué devuelve range(3)?", "0, 1, 2", [("0, 1, 2", "0, 1, 2"), ("1, 2, 3", "1, 2, 3"), ("0, 1, 2, 3", "0, 1, 2, 3"), ("3", "3")]),
    ],
    8: [
        ("¿Qué expresión comprueba si numero es par?", "numero % 2 == 0", [("numero % 2 == 0", "numero % 2 == 0"), ("numero / 2 == 0", "numero / 2 == 0"), ("numero % 2 == 1", "numero % 2 == 1"), ("numero // 2 == 0", "numero // 2 == 0")]),
        ("¿Qué permite revisar una segunda regla solo si la primera se cumple?", "if_anidado", [("if_anidado", "Un if dentro de otro if"), ("print", "Un print dentro de otro print"), ("elif_anidado", "Un elif dentro de otro elif"), ("while_anidado", "Un while dentro de otro while")]),
        ("Si numero no es positivo, ¿qué bloque puede manejar el caso?", "else", [("else", "else"), ("elif", "elif sin condición"), ("if", "if"), ("finally", "finally")]),
    ],
    9: [
        ("¿Cómo escribes una lista con 1 y 2?", "[1, 2]", [("[1, 2]", "[1, 2]"), ("(1, 2)", "(1, 2)"), ("{1, 2}", "{1, 2}"), ("{'1': 2}", "{'1': 2}")]),
        ("¿Qué índice tiene el primer elemento de una lista?", "0", [("0", "0"), ("1", "1"), ("-1", "-1"), ("2", "2")]),
        ("¿Qué método agrega un valor al final de frutas?", "append", [("append", "append()"), ("remove", "remove()"), ("extend", "extend()"), ("insert", "insert()")]),
    ],
    10: [
        ("¿Qué estructura guarda datos asociados a claves?", "diccionario", [("diccionario", "Diccionario"), ("tupla", "Tupla"), ("lista", "Lista"), ("conjunto", "Conjunto")]),
        ("¿Cuál colección no se puede modificar después de crearla?", "tupla", [("tupla", "Tupla"), ("lista", "Lista"), ("diccionario", "Diccionario"), ("conjunto", "Conjunto")]),
        ("¿Cómo obtienes el nombre de estudiante = {'nombre': 'Ana'}?", "estudiante['nombre']", [("estudiante['nombre']", "estudiante['nombre']"), ("estudiante.nombre", "estudiante.nombre"), ("estudiante[0]", "estudiante[0]"), ("estudiante['edad']", "estudiante['edad']")]),
    ],
    11: [
        ("¿Qué ciclo procesa cada nota de una lista?", "for", [("for", "for"), ("elif", "elif"), ("while", "while"), ("if", "if")]),
        ("¿Qué devuelve estudiante.items()?", "pares", [("pares", "Pares de clave y valor"), ("claves", "Solo las claves"), ("valores", "Solo los valores"), ("lista", "Una lista con solo los valores")]),
        ("¿Qué genera range(1, 4)?", "1, 2, 3", [("1, 2, 3", "1, 2, 3"), ("0, 1, 2, 3", "0, 1, 2, 3"), ("1, 2, 3, 4", "1, 2, 3, 4"), ("0, 1, 2", "0, 1, 2")]),
    ],
    12: [
        ("¿Cómo calculas el promedio de notas?", "suma_dividida", [("suma_dividida", "sum(notas) / len(notas)"), ("multiplicar", "sum(notas) * len(notas)"), ("maximo", "max(notas)"), ("minimo", "min(notas)")]),
        ("¿Qué método agrega una nueva nota a la lista?", "append", [("append", "append()"), ("items", "items()"), ("extend", "extend()"), ("pop", "pop()")]),
        ("¿Qué estructura relaciona el nombre de cada estudiante con sus notas?", "diccionario", [("diccionario", "Diccionario"), ("booleano", "Booleano"), ("lista", "Lista"), ("conjunto", "Conjunto")]),
    ],
    13: [
        ("¿Qué palabra define una función?", "def", [("def", "def"), ("class", "class"), ("lambda", "lambda"), ("return", "return")]),
        ("¿Cómo ejecutas una función llamada saludar?", "saludar()", [("saludar()", "saludar()"), ("def saludar", "def saludar"), ("saludar", "saludar"), ("call saludar", "call saludar")]),
        ("¿Qué instrucción devuelve un valor desde una función?", "return", [("return", "return"), ("print", "print"), ("break", "break"), ("yield", "yield")]),
    ],
    14: [
        ("En def sumar(a, b), ¿qué son a y b?", "parametros", [("parametros", "Parámetros"), ("argumentos", "Argumentos"), ("variables_locales", "Variables locales"), ("resultados", "Resultados")]),
        ("¿Qué devuelve return a + b?", "resultado", [("resultado", "El resultado de la suma"), ("texto", "Siempre un texto"), ("funcion", "La función completa"), ("ninguno", "Ningún valor")]),
        ("¿Qué argumentos recibe sumar(3, 4)?", "3_y_4", [("3_y_4", "3 y 4"), ("a_y_b", "Las palabras a y b"), ("7", "7"), ("texto", "Los textos '3' y '4'")]),
    ],
    15: [
        ("¿Cómo se llama una variable creada dentro de una función?", "local", [("local", "Local"), ("global", "Global"), ("parametro", "Parámetro"), ("argumento", "Argumento")]),
        ("¿Qué permite enviar un dato a una función sin depender de una global?", "parametro", [("parametro", "Un parámetro"), ("variable_global", "Una variable global"), ("retorno", "Un retorno"), ("local", "Una variable local")]),
        ("¿Dónde existe normalmente una variable local?", "funcion", [("funcion", "Dentro de su función"), ("todo_programa", "En todo el programa"), ("siguiente_linea", "Solo en la siguiente línea"), ("llamada", "Solo durante la llamada")]),
    ],
    16: [
        ("En el boletín, ¿qué devuelve clasificar(7.5)?", "Aprobado", [("Aprobado", "'Aprobado'"), ("Excelente", "'Excelente'"), ("Debe repasar", "'Debe repasar'"), ("7.5", "7.5")]),
        ("¿Qué entrega cada vuelta de for nombre, notas in estudiantes.items()?", "par", [("par", "Un estudiante y su lista de notas"), ("nombres", "Solo el nombre del estudiante"), ("nota", "Una sola nota"), ("todo", "El diccionario completo")]),
        ("¿Por qué calcular_promedio usa return en lugar de print?", "reutilizar", [("reutilizar", "Para usar el resultado en clasificar y en el print"), ("rapidez", "Porque return es más rápido que print"), ("obligatorio", "Porque una función no puede usar print"), ("mostrar", "Para mostrar el promedio dos veces")]),
    ],
}
