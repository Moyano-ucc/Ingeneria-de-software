import json
import random

from fastapi import APIRouter, Request

from models.ruta_model import RutaModel
from repositories.progress_repository import ProgressRepository
from security import csrf_protected
from views.responses import redirect, render_template


aprender_router = APIRouter(dependencies=csrf_protected)
progress_repository = ProgressRepository()


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


@aprender_router.api_route(
    "/aprender/ruta/{route_id}",
    methods=["GET", "POST"],
    name="aprender.ruta",
)
async def ruta(request: Request, route_id: str):
    if "usuario" not in request.session:
        return redirect(request.url_for("auth.login"))

    actividades = request.session.get("progreso", {})
    if route_id == "02":
        if not RutaModel.unidad_dos_desbloqueada(actividades):
            return redirect(request.url_for("aprender.mostrar_aprender"))

        lessons = [
            lesson
            for lesson in RutaModel.obtener_lecciones()
            if lesson["unit_id"] == 2
        ]
        normalized_activities = {
            lesson_id: (
                activity
                if isinstance(activity, dict)
                else {"completada": bool(activity)}
            )
            for lesson_id, activity in actividades.items()
        }
        if request.method == "POST":
            form = await request.form()
            try:
                selected_ids = json.loads(form.get("sequence", "[]"))
            except (TypeError, json.JSONDecodeError):
                selected_ids = []
            valid_ids = {piece["id"] for piece in RutaModel.PUZZLE_PIECES}
            if not isinstance(selected_ids, list):
                selected_ids = []
            selected_ids = list(
                dict.fromkeys(
                    piece_id
                    for piece_id in selected_ids
                    if isinstance(piece_id, str) and piece_id in valid_ids
                )
            )
            valid_sequence = (
                len(selected_ids) == len(valid_ids)
                and set(selected_ids) == valid_ids
            )
            completada = valid_sequence and selected_ids == RutaModel.PUZZLE_SOLUTION
            activity = {
                "completada": completada,
                "intentada": True,
                "puntuacion": int(completada),
                "total": 1,
            }
            actividades["unidad_02_puzzle"] = activity
            request.session["progreso"] = actividades
            progress_repository.save_activity(
                request.session["usuario"].get("id_persona"),
                "unidad_02_puzzle",
                activity,
            )
            request.session["puzzle_feedback"] = {
                "resultado": "correcto" if completada else "incorrecto",
                "selected_ids": selected_ids,
            }
            return redirect(
                request.url_for("aprender.ruta", route_id="02"),
                status_code=303,
            )

        feedback = request.session.pop("puzzle_feedback", None)
        resultado = None
        selected_ids = []
        if isinstance(feedback, dict):
            resultado = feedback.get("resultado")
            selected_ids = feedback.get("selected_ids", [])
            if not isinstance(selected_ids, list):
                selected_ids = []

        siguiente_unidad_desbloqueada = any(
            item["id"] == "03" and item["desbloqueada"]
            for item in RutaModel.obtener_rutas(actividades)
        )
        return render_template(
            request,
            "unidad_dos.html",
            pieces=RutaModel.PUZZLE_PIECES,
            lecciones=lessons,
            actividades=normalized_activities,
            selected_ids=selected_ids,
            resultado=resultado,
            siguiente_unidad_desbloqueada=siguiente_unidad_desbloqueada,
        )

    if route_id not in {"01", "03", "04"}:
        return redirect(request.url_for("aprender.mostrar_aprender"))
    unit_number = int(route_id)
    lecciones = [
        lesson
        for lesson in RutaModel.obtener_lecciones()
        if lesson["unit_id"] == unit_number
    ]
    rutas = RutaModel.obtener_rutas(actividades)
    ruta_actual = next((item for item in rutas if item["id"] == route_id), None)
    if ruta_actual is None or not ruta_actual["desbloqueada"]:
        return redirect(request.url_for("aprender.mostrar_aprender"))

    normalized_activities = {
        lesson_id: (
            activity
            if isinstance(activity, dict)
            else {"completada": bool(activity)}
        )
        for lesson_id, activity in actividades.items()
    }
    return render_template(
        request,
        "ruta.html",
        ruta_id=route_id,
        ruta=ruta_actual,
        lecciones=lecciones,
        actividades=normalized_activities,
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
        puzzle_completed = RutaModel.actividad_completada(
            actividades.get("unidad_02_puzzle", {})
        )
        if lesson["unit_id"] == 2 and not puzzle_completed:
            next_route_id = "02"
        elif lesson["unit_id"] < 4:
            next_route_id = f"{lesson['unit_id'] + 1:02d}"
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
    resultado = (
        _build_result(lesson, answers, actividades)
        if answers and len(answers) == len(lesson["answers"])
        else None
    )
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
