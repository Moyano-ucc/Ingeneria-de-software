import random

from fastapi import APIRouter, Request

from models.ruta_model import RutaModel
from repositories.progress_repository import ProgressRepository
from security import csrf_protected
from views.responses import redirect, render_template


aprender_router = APIRouter(dependencies=csrf_protected)
progress_repository = ProgressRepository()


def _normalize_activities(actividades):
    """Older sessions stored booleans; templates expect dictionaries."""
    return {
        lesson_id: (
            activity if isinstance(activity, dict) else {"completada": bool(activity)}
        )
        for lesson_id, activity in actividades.items()
    }


@aprender_router.get("/aprender", name="aprender.mostrar_aprender")
async def mostrar_aprender(request: Request):
    if "usuario" not in request.session:
        return redirect(request.url_for("auth.login"))

    rutas = RutaModel.obtener_rutas(request.session.get("progreso", {}))
    return render_template(
        request,
        "aprender.html",
        rutas=rutas,
        usuario=request.session["usuario"]["nombre"],
    )


@aprender_router.get("/aprender/ruta/{route_id}", name="aprender.ruta")
async def ruta(request: Request, route_id: str):
    if "usuario" not in request.session:
        return redirect(request.url_for("auth.login"))

    actividades = request.session.get("progreso", {})
    rutas = RutaModel.obtener_rutas(actividades)
    index = next((i for i, item in enumerate(rutas) if item["id"] == route_id), None)
    if index is None or not rutas[index]["desbloqueada"]:
        return redirect(request.url_for("aprender.mostrar_aprender"))

    siguiente = rutas[index + 1] if index + 1 < len(rutas) else None
    return render_template(
        request,
        "ruta.html",
        ruta_id=route_id,
        ruta=rutas[index],
        lecciones=[
            lesson
            for lesson in RutaModel.obtener_lecciones()
            if lesson["unit_id"] == int(route_id)
        ],
        actividades=_normalize_activities(actividades),
        siguiente_ruta=siguiente if siguiente and siguiente["desbloqueada"] else None,
    )


def _route_for_lesson(lesson, actividades):
    route_id = f"{lesson['unit_id']:02d}"
    route = next(
        (item for item in RutaModel.obtener_rutas(actividades) if item["id"] == route_id),
        None,
    )
    return route_id, route


def _next_step(lesson, actividades):
    """Return (next_lesson, next_route_id) after a passed quiz."""
    next_lesson = next(
        (
            item
            for item in RutaModel.obtener_lecciones()
            if item["unit_id"] == lesson["unit_id"]
            and item["numero"] > lesson["numero"]
            and not RutaModel.actividad_completada(actividades.get(item["id"], {}))
        ),
        None,
    )
    next_route_id = None
    if next_lesson is None:
        next_route = next(
            (
                route
                for route in RutaModel.obtener_rutas(actividades)
                if int(route["id"]) == lesson["unit_id"] + 1 and route["desbloqueada"]
            ),
            None,
        )
        next_route_id = next_route["id"] if next_route else None
    return next_lesson, next_route_id


def _last_answers(request: Request, lesson_id: str):
    """Answers of the latest quiz attempt (database first, session fallback)."""
    answers = progress_repository.find_last_answers(
        request.session["usuario"].get("id_persona"), lesson_id
    )
    if answers is None:
        answers = request.session.get("quiz_respuestas", {}).get(lesson_id)
    return answers if isinstance(answers, list) else None


def _build_result(lesson, answers, actividades):
    results = [
        answer == correct for answer, correct in zip(answers, lesson["answers"])
    ]
    score, total = sum(results), len(lesson["answers"])
    completada = score == total
    next_lesson, next_route_id = (
        _next_step(lesson, actividades) if completada else (None, None)
    )
    return {
        "score": score,
        "total": total,
        "results": results,
        "answers": answers,
        "completada": completada,
        "leccion_completada": RutaModel.actividad_completada(
            actividades.get(lesson["id"], {})
        ),
        "next_lesson": next_lesson,
        "next_route_id": next_route_id,
        "curso_completado": completada and all(
            route["completadas"] == route["total"]
            for route in RutaModel.obtener_rutas(actividades)
        ),
    }


@aprender_router.get(
    "/aprender/leccion/{lesson_id}",
    name="aprender.leccion",
)
async def leccion(request: Request, lesson_id: str):
    if "usuario" not in request.session:
        return redirect(request.url_for("auth.login"))

    lesson = RutaModel.obtener_leccion(lesson_id)
    if lesson is None:
        return redirect(request.url_for("aprender.mostrar_aprender"))
    for _question, options in lesson["questions"]:
        random.shuffle(options)
    actividades = request.session.get("progreso", {})
    route_id, route = _route_for_lesson(lesson, actividades)
    if route is None or not route["desbloqueada"]:
        return redirect(request.url_for("aprender.mostrar_aprender"))

    lessons = RutaModel.obtener_lecciones()
    index = next(i for i, item in enumerate(lessons) if item["id"] == lesson_id)
    if (
        index > 0
        and lessons[index - 1]["unit_id"] == lesson["unit_id"]
        and not RutaModel.actividad_completada(
            actividades.get(lessons[index - 1]["id"], {})
        )
    ):
        return redirect(request.url_for("aprender.ruta", route_id=route_id))

    # The last attempt is persisted, so going to the practice challenge and
    # coming back keeps the answers. ``?repetir=1`` shows an empty quiz to
    # start a new attempt (it is recorded only when the student submits it).
    repetir = request.query_params.get("repetir") == "1"
    answers = None if repetir else _last_answers(request, lesson_id)
    # A stored attempt is shown only if it still matches the current quiz
    # (questions can be updated after an attempt was saved).
    answers_match_quiz = bool(answers) and len(answers) == len(lesson["answers"]) and all(
        answer in {value for value, _label in options}
        for answer, (_question, options) in zip(answers, lesson["questions"])
    )
    resultado = _build_result(lesson, answers, actividades) if answers_match_quiz else None
    return render_template(
        request,
        "leccion.html",
        lesson=lesson,
        material=RutaModel.obtener_material_leccion(lesson_id),
        resultado=resultado,
        leccion_completada=RutaModel.actividad_completada(
            actividades.get(lesson_id, {})
        ),
    )


@aprender_router.post(
    "/aprender/leccion/{lesson_id}/completar",
    name="aprender.completar_leccion",
)
async def completar_leccion(request: Request, lesson_id: str):
    if "usuario" not in request.session:
        return redirect(request.url_for("auth.login"))

    lesson = RutaModel.obtener_leccion(lesson_id)
    if lesson is None:
        return redirect(request.url_for("aprender.mostrar_aprender"))
    progreso = request.session.get("progreso", {})
    _route_id, route = _route_for_lesson(lesson, progreso)
    if route is None or not route["desbloqueada"]:
        return redirect(request.url_for("aprender.mostrar_aprender"))

    form = await request.form()
    answers = [
        str(form.get(f"respuesta_{number}", ""))
        for number in range(1, len(lesson["answers"]) + 1)
    ]
    score = sum(
        answer == correct for answer, correct in zip(answers, lesson["answers"])
    )
    total = len(lesson["answers"])
    previous = progreso.get(lesson_id, {})
    # Repeating a lesson never undoes a previous completion.
    progreso[lesson_id] = {
        "completada": score == total or RutaModel.actividad_completada(previous),
        "intentada": True,
        "puntuacion": max(
            score,
            previous.get("puntuacion", 0) if isinstance(previous, dict) else 0,
        ),
        "total": total,
    }
    progress_repository.save_activity(
        request.session["usuario"].get("id_persona"),
        lesson_id,
        {**progreso[lesson_id], "puntuacion": score},
        answers=answers,
    )
    request.session["progreso"] = progreso
    quiz_respuestas = dict(request.session.get("quiz_respuestas", {}))
    quiz_respuestas[lesson_id] = answers
    request.session["quiz_respuestas"] = quiz_respuestas
    return redirect(
        request.url_for("aprender.leccion", lesson_id=lesson_id),
        status_code=303,
    )
