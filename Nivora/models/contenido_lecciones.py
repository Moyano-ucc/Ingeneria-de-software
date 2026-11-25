"""Theory shown in each lesson before the quiz.

Every entry follows the same structure so the template can render it:

- ``explicacion``: what the concept is and why it matters.
- ``analogia``: an everyday comparison that makes the idea concrete.
- ``ejemplo``: a short program.
- ``lineas``: what each line of the example does.
- ``salida``: what the example prints (``entrada`` shows typed input, if any).
- ``errores``: common mistakes with the reason and the fix.
- ``reto``: a "what does it print?" question; the answer is revealed on demand.
- ``proyecto`` (optional): brief, requirements and plan of a project lesson.
"""

LESSON_MATERIAL = {
    "variables": {
        "explicacion": (
            "Una variable es un nombre que apunta a un dato para poder usarlo más "
            "tarde. Se crea con el signo =, que en Python significa «guarda el valor "
            "de la derecha en el nombre de la izquierda» (no «es igual»). Python "
            "deduce el tipo del dato: int para enteros, float para decimales, str "
            "para texto entre comillas y bool para True o False."
        ),
        "analogia": (
            "Piensa en una caja con una etiqueta: la etiqueta es el nombre (edad) y "
            "lo que hay dentro es el valor (20). Puedes cambiar el contenido cuando "
            "quieras sin cambiar la etiqueta."
        ),
        "ejemplo": 'nombre = "Ana"\nedad = 20\naltura = 1.65\nactivo = True\nprint(nombre, edad, altura, activo)\nprint(type(edad))',
        "lineas": [
            ('nombre = "Ana"', "Guarda el texto Ana. Las comillas indican que es un str."),
            ("edad = 20", "Guarda el número entero 20 (int), sin comillas."),
            ("altura = 1.65", "Los decimales usan punto, no coma: es un float."),
            ("activo = True", "True y False (con mayúscula inicial) son valores bool."),
            ("print(nombre, edad, altura, activo)", "print muestra los valores separados por espacios."),
            ("print(type(edad))", "type indica el tipo del valor guardado en edad."),
        ],
        "salida": "Ana 20 1.65 True\n<class 'int'>",
        "errores": [
            {
                "codigo": "20 = edad",
                "problema": "El nombre siempre va a la izquierda del =.",
                "correccion": "edad = 20",
            },
            {
                "codigo": 'edad = "20"',
                "problema": "Con comillas, 20 es texto (str) y no podrás sumarlo como número.",
                "correccion": "edad = 20",
            },
            {
                "codigo": "mi edad = 20",
                "problema": "Los nombres no pueden tener espacios ni empezar con un número.",
                "correccion": "mi_edad = 20",
            },
        ],
        "reto": {
            "codigo": "puntos = 5\npuntos = puntos + 3\nprint(puntos)",
            "respuesta": "8",
            "explicacion": "Primero puntos vale 5; la segunda línea toma ese valor, le suma 3 y lo vuelve a guardar en puntos.",
        },
    },
    "operadores": {
        "explicacion": (
            "Los operadores aritméticos (+, -, *, /, //, %, **) calculan valores. "
            "Los operadores de comparación (==, !=, >, <, >=, <=) comparan dos "
            "valores y siempre devuelven True o False. Python respeta la jerarquía "
            "matemática: primero paréntesis, luego potencias, después * y / y al "
            "final + y -."
        ),
        "analogia": (
            "Es como una calculadora que además responde preguntas de sí o no: "
            "«¿7 es mayor que 5?» → True."
        ),
        "ejemplo": "total = 3 + 4\nmitad = total / 2\nentera = total // 2\nresto = total % 2\nprint(total, mitad, entera, resto)\nprint(total > 5, total == 7)",
        "lineas": [
            ("total = 3 + 4", "Suma y guarda 7 en total."),
            ("mitad = total / 2", "La división / siempre devuelve un decimal: 3.5."),
            ("entera = total // 2", "// divide y descarta los decimales: 3."),
            ("resto = total % 2", "% devuelve el residuo de la división: 1 (7 es impar)."),
            ("print(total, mitad, entera, resto)", "Muestra los cuatro resultados."),
            ("print(total > 5, total == 7)", "Las comparaciones producen valores bool."),
        ],
        "salida": "7 3.5 3 1\nTrue True",
        "errores": [
            {
                "codigo": "if total = 7:",
                "problema": "Un solo = asigna; para comparar se usan dos: ==.",
                "correccion": "if total == 7:",
            },
            {
                "codigo": "promedio = 8 + 6 / 2",
                "problema": "La división se hace antes que la suma, así que da 11.0 y no 7.0.",
                "correccion": "promedio = (8 + 6) / 2",
            },
        ],
        "reto": {
            "codigo": "print(2 + 3 * 4)\nprint(10 % 3)",
            "respuesta": "14\n1",
            "explicacion": "3 * 4 se calcula primero (12) y luego se suma 2. 10 entre 3 da 3 y sobra 1.",
        },
    },
    "entrada_salida": {
        "explicacion": (
            "print() muestra información en pantalla e input() espera a que la "
            "persona escriba algo y presione Enter. input siempre devuelve texto "
            "(str), aunque se escriban números, así que para calcular hay que "
            "convertirlo con int() o float(). Las f-strings (f\"...\") permiten "
            "insertar variables dentro de un texto usando llaves."
        ),
        "analogia": (
            "input es como un formulario que el programa te pide llenar, y print es "
            "la respuesta que el programa te devuelve."
        ),
        "ejemplo": 'nombre = input("Tu nombre: ")\nedad = int(input("Tu edad: "))\nprint(f"Hola {nombre}, el próximo año tendrás {edad + 1}")',
        "lineas": [
            ('nombre = input("Tu nombre: ")', "Muestra el mensaje, espera lo que escribas y lo guarda como texto."),
            ('edad = int(input("Tu edad: "))', "Lee el texto y lo convierte a entero para poder sumarle."),
            ('print(f"Hola {nombre}, ...")', "La f antes de las comillas reemplaza {nombre} y {edad + 1} por sus valores."),
        ],
        "entrada": ["Ana", "20"],
        "salida": "Tu nombre: Ana\nTu edad: 20\nHola Ana, el próximo año tendrás 21",
        "errores": [
            {
                "codigo": 'edad = input("Tu edad: ")\nprint(edad + 1)',
                "problema": "input devuelve texto; sumar texto y número produce un TypeError.",
                "correccion": 'edad = int(input("Tu edad: "))\nprint(edad + 1)',
            },
            {
                "codigo": 'print("Hola {nombre}")',
                "problema": "Sin la f delante, las llaves se muestran literalmente.",
                "correccion": 'print(f"Hola {nombre}")',
            },
        ],
        "reto": {
            "codigo": 'numero = "5"\nprint(numero * 3)',
            "respuesta": "555",
            "explicacion": "numero es texto, y multiplicar un texto lo repite: \"5\" tres veces.",
        },
    },
    "repaso_fundamentos": {
        "explicacion": (
            "Un programa completo suele seguir tres pasos: recibir datos (input), "
            "procesarlos (conversiones y operaciones) y mostrar el resultado "
            "(print). Identificar estos pasos antes de escribir te ayuda a "
            "organizar el código."
        ),
        "analogia": (
            "Como en una tienda: la cajera recibe el precio y la cantidad, calcula "
            "el total y te entrega el recibo."
        ),
        "ejemplo": 'precio = float(input("Precio: "))\ncantidad = int(input("Cantidad: "))\ntotal = precio * cantidad\nprint(f"Total a pagar: {total}")',
        "lineas": [
            ('precio = float(input("Precio: "))', "Entrada: el precio puede tener decimales, por eso float."),
            ('cantidad = int(input("Cantidad: "))', "Entrada: la cantidad es un número entero."),
            ("total = precio * cantidad", "Proceso: calcula el total."),
            ('print(f"Total a pagar: {total}")', "Salida: muestra el resultado con un mensaje claro."),
        ],
        "entrada": ["2.5", "4"],
        "salida": "Precio: 2.5\nCantidad: 4\nTotal a pagar: 10.0",
        "errores": [
            {
                "codigo": 'cantidad = int(input("Cantidad: "))  # escribe 2.5',
                "problema": "int() no acepta texto con decimales y lanza ValueError.",
                "correccion": "Usa float() cuando el dato pueda tener decimales.",
            },
        ],
        "reto": {
            "codigo": "a = 7\nb = 2\nprint(a // b, a % b)",
            "respuesta": "3 1",
            "explicacion": "7 // 2 es la parte entera (3) y 7 % 2 es lo que sobra (1).",
        },
    },
    "condicionales": {
        "explicacion": (
            "if permite que el programa tome decisiones: ejecuta un bloque solo si "
            "la condición es True. elif revisa otra condición si la anterior fue "
            "False, y else se ejecuta cuando ninguna se cumplió. Los dos puntos (:) "
            "y la sangría (4 espacios) indican qué líneas pertenecen a cada caso."
        ),
        "analogia": (
            "Como un semáforo: si está en verde avanzas, si está en amarillo "
            "reduces la velocidad y, en cualquier otro caso, te detienes."
        ),
        "ejemplo": "nota = 7\nif nota >= 9:\n    print('Excelente')\nelif nota >= 6:\n    print('Aprobado')\nelse:\n    print('Debes repasar')",
        "lineas": [
            ("nota = 7", "El dato que vamos a evaluar."),
            ("if nota >= 9:", "¿7 es mayor o igual que 9? No, se salta este bloque."),
            ("elif nota >= 6:", "¿7 es mayor o igual que 6? Sí, entra aquí."),
            ("    print('Aprobado')", "La sangría indica que esta línea pertenece al elif."),
            ("else:", "No se revisa: ya se cumplió una condición anterior."),
        ],
        "salida": "Aprobado",
        "errores": [
            {
                "codigo": "if nota >= 6\n    print('Aprobado')",
                "problema": "Faltan los dos puntos al final de la condición (SyntaxError).",
                "correccion": "if nota >= 6:\n    print('Aprobado')",
            },
            {
                "codigo": "if nota >= 6:\nprint('Aprobado')",
                "problema": "Sin sangría, Python no sabe que la línea pertenece al if (IndentationError).",
                "correccion": "if nota >= 6:\n    print('Aprobado')",
            },
        ],
        "reto": {
            "codigo": "edad = 15\nif edad >= 18:\n    print('Adulto')\nelif edad >= 13:\n    print('Adolescente')\nelse:\n    print('Niño')",
            "respuesta": "Adolescente",
            "explicacion": "15 no cumple >= 18, pero sí >= 13; else ya no se evalúa.",
        },
    },
    "while": {
        "explicacion": (
            "while repite un bloque mientras su condición sea True. Antes de cada "
            "vuelta vuelve a revisar la condición. Dentro del bloque debe cambiar "
            "algo (por ejemplo, un contador) para que en algún momento la condición "
            "sea False; si no, el ciclo nunca termina."
        ),
        "analogia": (
            "Como llenar un vaso: mientras no esté lleno, sigues sirviendo agua."
        ),
        "ejemplo": "contador = 3\nwhile contador > 0:\n    print(contador)\n    contador -= 1\nprint('¡Despegue!')",
        "lineas": [
            ("contador = 3", "Valor inicial del contador."),
            ("while contador > 0:", "Se repite mientras contador sea mayor que 0."),
            ("    print(contador)", "Muestra el valor actual: 3, luego 2, luego 1."),
            ("    contador -= 1", "Resta 1 (equivale a contador = contador - 1)."),
            ("print('¡Despegue!')", "Sin sangría: se ejecuta cuando el ciclo termina."),
        ],
        "salida": "3\n2\n1\n¡Despegue!",
        "errores": [
            {
                "codigo": "contador = 3\nwhile contador > 0:\n    print(contador)",
                "problema": "contador nunca cambia, así que el ciclo es infinito.",
                "correccion": "Agrega contador -= 1 dentro del bloque.",
            },
        ],
        "reto": {
            "codigo": "n = 1\nwhile n < 10:\n    n = n * 2\nprint(n)",
            "respuesta": "16",
            "explicacion": "n toma los valores 2, 4, 8 y 16; con 16 la condición n < 10 es False y el ciclo se detiene.",
        },
    },
    "for": {
        "explicacion": (
            "for recorre, uno por uno, los elementos de una secuencia (una lista, "
            "un texto o un range). La variable del ciclo toma cada valor en orden. "
            "range(inicio, fin) genera números desde inicio hasta fin - 1: el "
            "último número no se incluye."
        ),
        "analogia": (
            "Como pasar lista en clase: recorres los nombres en orden y haces lo "
            "mismo con cada uno."
        ),
        "ejemplo": "for numero in range(1, 4):\n    print(numero)\n\nfrutas = ['pera', 'uva']\nfor fruta in frutas:\n    print(f'Me gusta la {fruta}')",
        "lineas": [
            ("for numero in range(1, 4):", "numero toma los valores 1, 2 y 3 (el 4 no se incluye)."),
            ("    print(numero)", "Se ejecuta una vez por cada valor."),
            ("frutas = ['pera', 'uva']", "Una lista con dos elementos."),
            ("for fruta in frutas:", "fruta toma 'pera' y luego 'uva'."),
        ],
        "salida": "1\n2\n3\nMe gusta la pera\nMe gusta la uva",
        "errores": [
            {
                "codigo": "for i in range(1, 5):\n    print(i)  # se esperaba hasta 5",
                "problema": "range no incluye el último número: imprime del 1 al 4.",
                "correccion": "for i in range(1, 6):",
            },
        ],
        "reto": {
            "codigo": "suma = 0\nfor n in range(1, 4):\n    suma += n\nprint(suma)",
            "respuesta": "6",
            "explicacion": "Se suman 1 + 2 + 3; el 4 no se incluye en range(1, 4).",
        },
    },
    "control_rompecabezas": {
        "explicacion": (
            "Las condiciones pueden anidarse: un if dentro de otro if. La sangría "
            "indica el nivel: cada bloque interno lleva 4 espacios más que su "
            "condición. Combinar condiciones con ciclos permite resolver problemas "
            "más completos, como clasificar varios números."
        ),
        "analogia": (
            "Como un formulario con preguntas condicionales: «¿Tienes mascota? Si "
            "respondiste sí, ¿es un perro o un gato?»."
        ),
        "ejemplo": "numero = 8\nif numero > 0:\n    if numero % 2 == 0:\n        print('positivo y par')\n    else:\n        print('positivo e impar')\nelse:\n    print('no positivo')",
        "lineas": [
            ("if numero > 0:", "Primera pregunta: ¿es positivo?"),
            ("    if numero % 2 == 0:", "Solo si es positivo: ¿el residuo entre 2 es 0? Entonces es par."),
            ("        print('positivo y par')", "8 espacios: pertenece al if interno."),
            ("    else:", "Alternativa del if interno (positivo pero impar)."),
            ("else:", "Alternativa del if externo (cero o negativo)."),
        ],
        "salida": "positivo y par",
        "errores": [
            {
                "codigo": "if numero > 0:\n    if numero % 2 == 0:\n    print('par')",
                "problema": "El print debe tener más sangría que el if interno.",
                "correccion": "        print('par')",
            },
        ],
        "reto": {
            "codigo": "for n in [3, -2, 4]:\n    if n > 0:\n        if n % 2 == 0:\n            print('par')\n        else:\n            print('impar')",
            "respuesta": "impar\npar",
            "explicacion": "3 es positivo e impar; -2 no entra al primer if; 4 es positivo y par.",
        },
    },
    "listas": {
        "explicacion": (
            "Una lista guarda varios valores en orden dentro de corchetes. Cada "
            "elemento tiene una posición (índice) que empieza en 0. Las listas se "
            "pueden modificar: append agrega al final, remove elimina un valor y "
            "len indica cuántos elementos hay."
        ),
        "analogia": (
            "Como una lista de compras numerada desde cero: puedes consultar un "
            "renglón, agregar productos al final o tachar uno."
        ),
        "ejemplo": "frutas = ['pera', 'uva']\nfrutas.append('mango')\nprint(frutas)\nprint(frutas[0], frutas[-1])\nprint(len(frutas))",
        "lineas": [
            ("frutas = ['pera', 'uva']", "Lista con dos elementos: índice 0 es 'pera', índice 1 es 'uva'."),
            ("frutas.append('mango')", "Agrega 'mango' al final."),
            ("print(frutas[0], frutas[-1])", "El índice -1 accede al último elemento."),
            ("print(len(frutas))", "Cantidad de elementos: 3."),
        ],
        "salida": "['pera', 'uva', 'mango']\npera mango\n3",
        "errores": [
            {
                "codigo": "frutas = ['pera', 'uva']\nprint(frutas[2])",
                "problema": "Con 2 elementos los índices válidos son 0 y 1 (IndexError).",
                "correccion": "print(frutas[1])",
            },
        ],
        "reto": {
            "codigo": "numeros = [4, 7, 9]\nnumeros.append(1)\nprint(numeros[1] + numeros[-1])",
            "respuesta": "8",
            "explicacion": "numeros[1] es 7 y numeros[-1] es el 1 que se agregó al final.",
        },
    },
    "estructuras": {
        "explicacion": (
            "Una tupla se escribe con paréntesis y no se puede modificar después de "
            "crearla: sirve para datos fijos, como coordenadas. Un diccionario usa "
            "llaves {} y guarda pares clave: valor; se consulta por la clave en vez "
            "de por la posición."
        ),
        "analogia": (
            "Un diccionario es como una agenda de contactos: buscas por el nombre "
            "(clave) y obtienes el teléfono (valor)."
        ),
        "ejemplo": "coordenada = (4, 7)\nestudiante = {'nombre': 'Ana', 'edad': 20}\nestudiante['edad'] = 21\nprint(coordenada[0])\nprint(estudiante['nombre'], estudiante['edad'])",
        "lineas": [
            ("coordenada = (4, 7)", "Tupla: dos valores que no cambiarán."),
            ("estudiante = {'nombre': 'Ana', 'edad': 20}", "Diccionario con dos claves."),
            ("estudiante['edad'] = 21", "Cambia el valor asociado a la clave 'edad'."),
            ("print(coordenada[0])", "Las tuplas también usan índices desde 0."),
        ],
        "salida": "4\nAna 21",
        "errores": [
            {
                "codigo": "coordenada = (4, 7)\ncoordenada[0] = 5",
                "problema": "Las tuplas no se pueden modificar (TypeError).",
                "correccion": "Usa una lista si necesitas cambiar los valores.",
            },
            {
                "codigo": "print(estudiante['apellido'])",
                "problema": "Si la clave no existe, Python lanza KeyError.",
                "correccion": "print(estudiante.get('apellido', 'sin dato'))",
            },
        ],
        "reto": {
            "codigo": "precios = {'pan': 2, 'leche': 3}\nprecios['pan'] = 4\nprint(precios['pan'] + precios['leche'])",
            "respuesta": "7",
            "explicacion": "El precio del pan cambió a 4; 4 + 3 = 7.",
        },
    },
    "recorrido": {
        "explicacion": (
            "Un for recorre los elementos de una lista directamente. Para "
            "diccionarios, .items() entrega cada par clave y valor, que se pueden "
            "recibir en dos variables. Es común usar una variable acumuladora para "
            "sumar o contar mientras se recorre."
        ),
        "analogia": (
            "Como revisar uno por uno los exámenes de un grupo e ir sumando las "
            "notas para luego sacar el promedio."
        ),
        "ejemplo": "notas = [8, 9, 10]\ntotal = 0\nfor nota in notas:\n    total += nota\nprint(total)\n\nestudiante = {'nombre': 'Ana', 'edad': 20}\nfor clave, valor in estudiante.items():\n    print(clave, valor)",
        "lineas": [
            ("total = 0", "Acumulador: empieza en 0 antes del ciclo."),
            ("for nota in notas:", "nota toma 8, 9 y 10."),
            ("    total += nota", "Suma cada nota al acumulador."),
            ("for clave, valor in estudiante.items():", "Recorre los pares del diccionario."),
        ],
        "salida": "27\nnombre Ana\nedad 20",
        "errores": [
            {
                "codigo": "for nota in notas:\n    total = 0\n    total += nota",
                "problema": "El acumulador se reinicia en cada vuelta y solo queda la última nota.",
                "correccion": "Crea total = 0 antes del for.",
            },
        ],
        "reto": {
            "codigo": "contador = 0\nfor letra in 'hola':\n    contador += 1\nprint(contador)",
            "respuesta": "4",
            "explicacion": "Un texto también se recorre: el ciclo da una vuelta por cada letra.",
        },
    },
    "proyecto_estructuras": {
        "explicacion": (
            "Las estructuras se combinan: un diccionario puede guardar listas como "
            "valores. Así se representan registros reales, como las notas de cada "
            "estudiante. sum() suma una lista y len() cuenta sus elementos, lo que "
            "permite calcular promedios."
        ),
        "analogia": (
            "Como una planilla: cada fila es un estudiante (clave) y sus columnas "
            "son las notas (lista)."
        ),
        "ejemplo": "notas = {'Ana': [8, 9], 'Luis': [7, 10]}\nfor nombre, valores in notas.items():\n    promedio = sum(valores) / len(valores)\n    print(nombre, promedio)",
        "lineas": [
            ("notas = {'Ana': [8, 9], 'Luis': [7, 10]}", "Cada clave (nombre) guarda una lista de notas."),
            ("for nombre, valores in notas.items():", "Recorre cada estudiante y su lista."),
            ("    promedio = sum(valores) / len(valores)", "Suma las notas y divide por la cantidad."),
            ("    print(nombre, promedio)", "Muestra el resultado de cada estudiante."),
        ],
        "salida": "Ana 8.5\nLuis 8.5",
        "errores": [
            {
                "codigo": "promedio = sum(valores) / 2",
                "problema": "Si cambia la cantidad de notas, el resultado será incorrecto.",
                "correccion": "promedio = sum(valores) / len(valores)",
            },
        ],
        "reto": {
            "codigo": "inventario = {'lapices': [3, 2], 'gomas': [1]}\nprint(sum(inventario['lapices']))",
            "respuesta": "5",
            "explicacion": "inventario['lapices'] es la lista [3, 2] y su suma es 5.",
        },
    },
    "funciones": {
        "explicacion": (
            "Una función agrupa instrucciones bajo un nombre para reutilizarlas. Se "
            "define con def, el nombre, paréntesis y dos puntos; su cuerpo lleva "
            "sangría. Definirla no la ejecuta: hay que llamarla escribiendo su "
            "nombre seguido de paréntesis."
        ),
        "analogia": (
            "Una receta: la escribes una vez (def) y la preparas cada vez que la "
            "necesitas (llamada)."
        ),
        "ejemplo": "def saludar():\n    print('Hola')\n    print('Bienvenida a Nivora')\n\nsaludar()\nsaludar()",
        "lineas": [
            ("def saludar():", "Define la función; todavía no muestra nada."),
            ("    print('Hola')", "Cuerpo de la función (con sangría)."),
            ("saludar()", "Llama a la función: ejecuta su cuerpo."),
            ("saludar()", "Puede llamarse cuantas veces se necesite."),
        ],
        "salida": "Hola\nBienvenida a Nivora\nHola\nBienvenida a Nivora",
        "errores": [
            {
                "codigo": "def saludar():\n    print('Hola')\n\nsaludar",
                "problema": "Sin paréntesis la función no se ejecuta.",
                "correccion": "saludar()",
            },
            {
                "codigo": "saludar()\n\ndef saludar():\n    print('Hola')",
                "problema": "La función debe definirse antes de llamarla (NameError).",
                "correccion": "Escribe el def antes de la llamada.",
            },
        ],
        "reto": {
            "codigo": "def aplaudir():\n    print('👏')\n\nprint('Inicio')\naplaudir()",
            "respuesta": "Inicio\n👏",
            "explicacion": "El def solo define; lo primero que se ejecuta es print('Inicio') y luego la llamada.",
        },
    },
    "parametros": {
        "explicacion": (
            "Los parámetros son variables que la función recibe entre paréntesis. "
            "Al llamarla se envían argumentos, que ocupan esos parámetros en orden. "
            "return devuelve un resultado al lugar de la llamada para que pueda "
            "guardarse o usarse en otra operación; print solo lo muestra."
        ),
        "analogia": (
            "Una licuadora: los ingredientes son los parámetros y el batido que "
            "sale es el valor que devuelve return."
        ),
        "ejemplo": "def sumar(a, b):\n    return a + b\n\nresultado = sumar(3, 4)\nprint(resultado)\nprint(sumar(10, 5) * 2)",
        "lineas": [
            ("def sumar(a, b):", "a y b son parámetros: recibirán valores."),
            ("    return a + b", "Devuelve la suma al lugar de la llamada."),
            ("resultado = sumar(3, 4)", "3 va a a, 4 va a b; el 7 devuelto se guarda."),
            ("print(sumar(10, 5) * 2)", "El valor devuelto (15) se usa en otra operación."),
        ],
        "salida": "7\n30",
        "errores": [
            {
                "codigo": "def sumar(a, b):\n    print(a + b)\n\ntotal = sumar(3, 4) * 2",
                "problema": "Sin return la función devuelve None y la multiplicación falla.",
                "correccion": "    return a + b",
            },
            {
                "codigo": "sumar(3)",
                "problema": "Faltan argumentos: la función espera dos (TypeError).",
                "correccion": "sumar(3, 4)",
            },
        ],
        "reto": {
            "codigo": "def doble(n):\n    return n * 2\n\nprint(doble(doble(3)))",
            "respuesta": "12",
            "explicacion": "doble(3) devuelve 6 y luego doble(6) devuelve 12.",
        },
    },
    "alcance": {
        "explicacion": (
            "Las variables creadas dentro de una función son locales: solo existen "
            "mientras la función se ejecuta. Las variables definidas fuera son "
            "globales. Para que una función sea fácil de entender y reutilizar, "
            "recibe los datos como parámetros y entrega el resultado con return."
        ),
        "analogia": (
            "Lo que escribes en la pizarra de un salón (función) se borra al salir; "
            "si quieres conservarlo, lo anotas y lo llevas contigo (return)."
        ),
        "ejemplo": "def calcular_total(precio, cantidad):\n    total = precio * cantidad\n    return total\n\nresultado = calcular_total(5, 3)\nprint(resultado)",
        "lineas": [
            ("def calcular_total(precio, cantidad):", "precio y cantidad son locales a la función."),
            ("    total = precio * cantidad", "total también es local."),
            ("    return total", "El valor sale de la función con return."),
            ("resultado = calcular_total(5, 3)", "Fuera, el valor devuelto se guarda en otra variable."),
        ],
        "salida": "15",
        "errores": [
            {
                "codigo": "def calcular():\n    total = 15\n\ncalcular()\nprint(total)",
                "problema": "total solo existe dentro de la función (NameError).",
                "correccion": "Devuelve el valor con return y guárdalo: total = calcular()",
            },
        ],
        "reto": {
            "codigo": "x = 10\ndef cambiar():\n    x = 99\n    return x\n\ncambiar()\nprint(x)",
            "respuesta": "10",
            "explicacion": "La x de dentro es local y distinta de la global; la global sigue valiendo 10.",
        },
    },
    "proyecto_final": {
        "explicacion": (
            "En este proyecto construirás un programa completo: un boletín de "
            "calificaciones. Para resolverlo usarás todo lo que aprendiste en el "
            "curso: variables y operadores (unidad 1), condicionales y ciclos "
            "(unidad 2), listas y diccionarios (unidad 3) y funciones (unidad 4). "
            "La clave es dividir el problema en partes pequeñas y resolver cada "
            "una con una función."
        ),
        "analogia": (
            "Es lo que hace un profesor al cerrar el periodo: tiene las notas de "
            "cada estudiante, calcula su promedio, decide si aprobó y entrega un "
            "boletín con el resultado."
        ),
        "proyecto": {
            "enunciado": (
                "Escribe un programa que reciba las notas de varios estudiantes y "
                "muestre, para cada uno, su promedio con un decimal y su "
                "clasificación."
            ),
            "requisitos": [
                "Guardar a cada estudiante con su lista de notas en un diccionario.",
                "Crear una función calcular_promedio(notas) que devuelva el promedio.",
                "Crear una función clasificar(promedio) que devuelva «Excelente» (9 o más), «Aprobado» (6 o más) o «Debe repasar».",
                "Recorrer el diccionario con un ciclo for y mostrar una línea por estudiante.",
            ],
            "plan": [
                "Datos: ¿cómo guardo los estudiantes y sus notas? → un diccionario de listas.",
                "Cálculo: ¿qué se repite para cada estudiante? → el promedio, en una función.",
                "Decisión: ¿cómo elijo el mensaje? → if, elif y else dentro de otra función.",
                "Resultado: recorro el diccionario y muestro cada línea con una f-string.",
            ],
        },
        "ejemplo": "def calcular_promedio(notas):\n    return sum(notas) / len(notas)\n\ndef clasificar(promedio):\n    if promedio >= 9:\n        return 'Excelente'\n    elif promedio >= 6:\n        return 'Aprobado'\n    else:\n        return 'Debe repasar'\n\nestudiantes = {'Ana': [9, 10, 8], 'Luis': [6, 5, 7], 'Sofía': [4, 6, 5]}\n\nfor nombre, notas in estudiantes.items():\n    promedio = calcular_promedio(notas)\n    print(f'{nombre}: {promedio:.1f} - {clasificar(promedio)}')",
        "lineas": [
            ("def calcular_promedio(notas):", "Unidad 4: una función con una sola tarea, calcular."),
            ("    return sum(notas) / len(notas)", "Unidad 3: sum y len trabajan sobre la lista de notas."),
            ("def clasificar(promedio):", "Una segunda función, solo para decidir el mensaje."),
            ("    if promedio >= 9: ... elif ... else:", "Unidad 2: las condiciones se revisan en orden, de la más exigente a la menos."),
            ("estudiantes = {'Ana': [9, 10, 8], ...}", "Unidad 3: cada clave es un nombre y su valor, una lista de notas."),
            ("for nombre, notas in estudiantes.items():", "Unidad 2 y 3: recorre cada par nombre–notas."),
            ("    promedio = calcular_promedio(notas)", "Se reutiliza la función con las notas de cada estudiante."),
            ("    print(f'{nombre}: {promedio:.1f} - ...')", "Unidad 1: f-string; :.1f muestra un decimal."),
        ],
        "salida": "Ana: 9.0 - Excelente\nLuis: 6.0 - Aprobado\nSofía: 5.0 - Debe repasar",
        "errores": [
            {
                "codigo": "def calcular_promedio(notas):\n    print(sum(notas) / len(notas))",
                "problema": "Con print la función muestra el número pero devuelve None, y clasificar(None) falla.",
                "correccion": "    return sum(notas) / len(notas)",
            },
            {
                "codigo": "if promedio >= 6:\n    return 'Aprobado'\nelif promedio >= 9:\n    return 'Excelente'",
                "problema": "Un 9.5 también cumple >= 6, así que nunca llegaría a «Excelente». El orden de las condiciones importa.",
                "correccion": "Revisa primero la condición más exigente (>= 9).",
            },
            {
                "codigo": "for nombre in estudiantes:\n    promedio = calcular_promedio(nombre)",
                "problema": "Recorrer el diccionario sin .items() entrega solo las claves (los nombres), no las notas.",
                "correccion": "for nombre, notas in estudiantes.items():",
            },
        ],
        "reto": {
            "codigo": "def clasificar(promedio):\n    if promedio >= 9:\n        return 'Excelente'\n    elif promedio >= 6:\n        return 'Aprobado'\n    return 'Debe repasar'\n\nnotas = [10, 8, 9]\nprint(clasificar(sum(notas) / len(notas)))",
            "respuesta": "Excelente",
            "explicacion": "El promedio de 10, 8 y 9 es 9.0; cumple la primera condición (>= 9), así que devuelve «Excelente».",
        },
    },
}
