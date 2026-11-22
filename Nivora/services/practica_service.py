"""Evaluation and guided feedback for practice exercises.

Student code is never executed. It is parsed with :mod:`ast` and compared
structurally with the expected answer, so spacing, quote style or redundant
parentheses do not matter. When the answer is wrong, the feedback explains
what is missing or why it is incorrect without revealing the full solution.
"""

import ast
import json


MAX_CODE_LENGTH = 2_000

OPERATOR_NAMES = {
    ast.Add: "sumar (+)",
    ast.Sub: "restar (-)",
    ast.Mult: "multiplicar (*)",
    ast.Div: "dividir (/)",
}


# --------------------------------------------------------------------------
# Code exercises (easy level: written code or blocks)
# --------------------------------------------------------------------------

class _Normalizer(ast.NodeTransformer):
    """Make equivalent programs produce the same AST."""

    def __init__(self, any_input_message=False):
        self.any_input_message = any_input_message

    def visit_Call(self, node):
        self.generic_visit(node)
        if (
            self.any_input_message
            and isinstance(node.func, ast.Name)
            and node.func.id == "input"
        ):
            node.args = [
                ast.Constant("<mensaje>")
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                else arg
                for arg in node.args
            ]
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        # a + b == b + a and a * b == b * a
        if isinstance(node.op, (ast.Add, ast.Mult)):
            left, right = sorted((node.left, node.right), key=ast.dump)
            node.left, node.right = left, right
        return node

    def visit_Module(self, node):
        self.generic_visit(node)
        # The order of consecutive constant assignments does not matter.
        body, group = [], []
        for statement in node.body:
            if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Constant):
                group.append(statement)
                continue
            body.extend(sorted(group, key=ast.dump))
            group = []
            body.append(statement)
        body.extend(sorted(group, key=ast.dump))
        node.body = body
        return node


def _normalized_dump(tree, any_input_message):
    return ast.dump(_Normalizer(any_input_message).visit(tree), annotate_fields=False)


def _assignments(tree):
    return {
        statement.targets[0].id: statement.value
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
    }


def _print_calls(tree):
    return [
        statement.value
        for statement in tree.body
        if isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Name)
        and statement.value.func.id == "print"
    ]


def _call_name(node):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def _syntax_feedback(error):
    message = (error.msg or "").lower()
    line = f"la línea {error.lineno}" if error.lineno else "tu código"
    if "unterminated string" in message or "eol while scanning" in message:
        tip = "Parece que falta cerrar unas comillas."
    elif "never closed" in message or "unexpected eof" in message:
        tip = "Parece que falta cerrar un paréntesis."
    elif "unmatched" in message:
        tip = "Hay un paréntesis de cierre que sobra."
    elif "cannot assign to literal" in message or "cannot assign to" in message:
        tip = "El nombre de la variable debe ir a la izquierda del = y el valor a la derecha."
    elif "maybe you meant '==' or ':='" in message or "invalid syntax" in message:
        tip = "Revisa el orden de los elementos: nombre, luego =, luego el valor."
    elif "indent" in message:
        tip = "Revisa la sangría: estas líneas no deben empezar con espacios."
    else:
        tip = "Compara tu línea con el formato que indican los pasos."
    return f"Python no puede leer {line}. {tip}"


def _value_feedback(name, expected, actual):
    if isinstance(expected, ast.Constant) and isinstance(actual, ast.Constant):
        if isinstance(actual.value, str) and not isinstance(expected.value, str) and (
            actual.value.strip() == str(expected.value)
        ):
            return (
                f"Escribiste el valor de «{name}» entre comillas, así que Python lo "
                "guarda como texto. Quita las comillas para que sea un número."
            )
        return f"El valor que guardas en «{name}» no es el que pide el enunciado."
    if isinstance(expected, ast.BinOp):
        if isinstance(actual, ast.Constant):
            return (
                f"En «{name}» escribiste el resultado a mano. Escribe la operación "
                "para que Python haga el cálculo."
            )
        if isinstance(actual, ast.BinOp) and type(actual.op) is not type(expected.op):
            wanted = OPERATOR_NAMES.get(type(expected.op), "otra operación")
            return f"Revisa el operador de «{name}»: el enunciado pide {wanted}."
        return f"La operación que guardas en «{name}» usa valores distintos a los del enunciado."
    expected_call = _call_name(expected)
    if expected_call:
        actual_call = _call_name(actual)
        if actual_call is None:
            return f"Para obtener «{name}» debes llamar a la función {expected_call}()."
        if actual_call != expected_call:
            return (
                f"Usaste {actual_call}(), pero aquí se necesita {expected_call}(). "
                "input() recibe datos; print() los muestra."
            )
        return f"Revisa lo que escribiste dentro de {expected_call}()."
    return f"El valor que guardas en «{name}» no es el esperado."


def _diagnose(expected_tree, tree):
    expected_assigns = _assignments(expected_tree)
    actual_assigns = _assignments(tree)
    messages = []

    for statement in tree.body:
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Compare)
            and any(isinstance(op, ast.Eq) for op in statement.value.ops)
        ):
            messages.append(
                "Usaste == , que sirve para comparar. Para guardar un valor en una "
                "variable usa un solo =."
            )
            break

    for name, expected_value in expected_assigns.items():
        if name in actual_assigns:
            if ast.dump(_Normalizer(True).visit(actual_assigns[name])) != ast.dump(
                _Normalizer(True).visit(expected_value)
            ):
                messages.append(_value_feedback(name, expected_value, actual_assigns[name]))
            continue
        similar = next((n for n in actual_assigns if n.lower() == name.lower()), None)
        if similar:
            messages.append(
                f"Python distingue mayúsculas y minúsculas: la variable debe llamarse "
                f"«{name}», no «{similar}»."
            )
        elif not messages:
            messages.append(f"Falta crear la variable «{name}».")

    expected_prints = _print_calls(expected_tree)
    actual_prints = _print_calls(tree)
    if expected_prints and not actual_prints:
        messages.append("Falta mostrar el resultado con print().")
    elif expected_prints and actual_prints and not messages:
        messages.append(
            "Revisa lo que muestras con print(): debe ser el resultado del cálculo "
            "usando tus variables."
        )

    if not messages:
        messages.append(
            "Tu código es válido, pero no hace exactamente lo que pide el reto. "
            "Relee los pasos y compáralos con cada línea."
        )
    return messages[:2]


def evaluate_code(exercise, code):
    """Return ``(correct, feedback_messages)`` for a code exercise."""
    code = (code or "").replace("\r\n", "\n").strip()
    if not code:
        return False, ["Todavía no escribiste código. Sigue el paso 1 para empezar."]
    if len(code) > MAX_CODE_LENGTH:
        return False, ["Tu respuesta es demasiado larga para este reto."]
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return False, [_syntax_feedback(error)]

    any_message = bool(exercise.get("acepta_cualquier_mensaje"))
    expected_tree = ast.parse(exercise["respuesta"])
    if _normalized_dump(tree, any_message) == _normalized_dump(expected_tree, any_message):
        return True, []
    return False, _diagnose(ast.parse(exercise["respuesta"]), ast.parse(code))


# --------------------------------------------------------------------------
# Puzzle exercises (ordenar, completar, emparejar)
# --------------------------------------------------------------------------

def validate_puzzle_answer(exercise, raw_answer):
    """Return ``(normalized_answer, correct)``; unknown pieces are discarded."""
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
            [item for item in answer if isinstance(item, str) and item in valid_ids][
                : len(valid_ids)
            ]
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
    else:
        valid_right = {item["id"] for item in puzzle["derecha"]}
        options = {item["id"]: valid_right for item in puzzle["izquierda"]}

    normalized = (
        {
            key: value
            for key, value in answer.items()
            if key in options and isinstance(value, str) and value in options[key]
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


INVALID_PIECES_MESSAGE = (
    "Tu respuesta incluye piezas que no pertenecen a este reto. Pulsa «Limpiar» "
    "y vuelve a armarla."
)


def puzzle_feedback(exercise, answer):
    """Explain what is wrong in a puzzle answer without solving it."""
    puzzle = exercise["rompecabezas"]
    kind = exercise["tipo"]
    if answer == puzzle["solucion"]:
        return [INVALID_PIECES_MESSAGE]

    if kind == "ordenar":
        solution = puzzle["solucion"]
        texts = {block["id"]: block["texto"] for block in puzzle["bloques"]}
        if len(answer) < len(solution):
            return [f"Usa todos los bloques: te faltan {len(solution) - len(answer)}."]
        in_place = sum(a == b for a, b in zip(answer, solution))
        messages = [f"{in_place} de {len(solution)} bloques están en su lugar."]
        wrong = next(i for i, (a, b) in enumerate(zip(answer, solution)) if a != b)
        messages.append(f"Revisa la línea {wrong + 1}: «{texts[answer[wrong]].strip()}».")
        if texts[answer[wrong]].startswith(" ") or texts[solution[wrong]].startswith(" "):
            messages.append(
                "Recuerda: una línea con sangría va justo debajo de la línea terminada "
                "en «:» a la que pertenece."
            )
        return messages

    if kind == "completar":
        explanations = puzzle.get("explicaciones", {})
        labels = {
            gap["id"]: {option["id"]: option["texto"] for option in gap["opciones"]}
            for gap in puzzle["huecos"]
        }
        missing = [gap for gap in puzzle["solucion"] if gap not in answer]
        if missing:
            return ["Elige una ficha para cada hueco antes de comprobar."]
        messages = []
        for gap, expected in puzzle["solucion"].items():
            chosen = answer.get(gap)
            if chosen != expected:
                messages.append(
                    explanations.get(gap, {}).get(chosen)
                    or f"La ficha «{labels[gap][chosen]}» no produce el resultado esperado."
                )
        return messages

    left = {item["id"]: item["texto"] for item in puzzle["izquierda"]}
    solution = puzzle["solucion"]
    if len(answer) < len(solution):
        return [f"Te faltan {len(solution) - len(answer)} parejas por conectar."]
    correct_pairs = sum(answer.get(key) == value for key, value in solution.items())
    first_wrong = next(key for key, value in solution.items() if answer.get(key) != value)
    return [
        f"Tienes {correct_pairs} de {len(solution)} parejas correctas.",
        f"Revisa con qué conectaste «{left[first_wrong]}».",
    ]
