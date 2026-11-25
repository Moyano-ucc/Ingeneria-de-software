from fastapi import APIRouter, Request

from models.ejercicios_practica import EJERCICIOS
from security import csrf_protected
from services.practica_service import (
    evaluate_code,
    puzzle_feedback,
    validate_puzzle_answer,
)
from views.responses import redirect, render_template


practica_router = APIRouter(dependencies=csrf_protected)
ATTEMPTS_KEY = "practice_attempts"


def _find_exercise(exercise_id):
    return next(
        (item for item in EJERCICIOS if item["id"] == exercise_id),
        EJERCICIOS[0],
    )


@practica_router.api_route(
    "/practica",
    methods=["GET", "POST"],
    name="practica.mostrar_practica",
)
async def mostrar_practica(request: Request):
    if "usuario" not in request.session:
        return redirect(request.url_for("auth.login"))

    if request.method == "POST":
        form = await request.form()
        ejercicio = _find_exercise(form.get("ejercicio"))
        if "tipo" in ejercicio:
            answer, correct = validate_puzzle_answer(ejercicio, form.get("respuesta", ""))
            feedback = [] if correct else puzzle_feedback(ejercicio, answer)
            result = {"respuesta": answer}
        else:
            codigo = str(form.get("codigo", "")).strip()
            correct, feedback = evaluate_code(ejercicio, codigo)
            result = {"codigo": codigo, "modo": form.get("modo", "")}

        # Failed attempts unlock the next hint automatically.
        attempts = dict(request.session.get(ATTEMPTS_KEY, {}))
        attempts[ejercicio["id"]] = 0 if correct else attempts.get(ejercicio["id"], 0) + 1
        request.session[ATTEMPTS_KEY] = attempts
        request.session["practice_result"] = {
            "ejercicio_id": ejercicio["id"],
            "correcto": correct,
            "retroalimentacion": feedback,
            **result,
        }
        destination = request.url_for("practica.mostrar_practica").include_query_params(
            ejercicio=ejercicio["id"]
        )
        return redirect(destination, status_code=303)

    ejercicio = _find_exercise(request.query_params.get("ejercicio", "variables"))
    stored = request.session.pop("practice_result", None)
    resultado = (
        stored
        if isinstance(stored, dict) and stored.get("ejercicio_id") == ejercicio["id"]
        else None
    )
    intentos = request.session.get(ATTEMPTS_KEY, {}).get(ejercicio["id"], 0)
    return render_template(
        request,
        "practica.html",
        ejercicios=EJERCICIOS,
        ejercicio=ejercicio,
        resultado=resultado,
        intentos=intentos,
        pistas_visibles=min(1 + intentos, len(ejercicio["pistas"])),
    )
