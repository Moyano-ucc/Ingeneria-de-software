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
        return redirect(str(request.url_for("auth.login")))

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
        return redirect(str(request.url_for("auth.login")))

    actividades = request.session.get("progreso", {})
    if route_id == "02":
        if not RutaModel.unidad_dos_desbloqueada(actividades):
            return redirect(str(request.url_for("aprender.mostrar_aprender")))

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
                str(request.url_for("aprender.ruta", route_id="02")),
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
        return redirect(str(request.url_for("aprender.mostrar_aprender")))
    unit_number = int(route_id)
    lecciones = [
        lesson
        for lesson in RutaModel.obtener_lecciones()
        if lesson["unit_id"] == unit_number
    ]
    rutas = RutaModel.obtener_rutas(actividades)
    ruta_actual = next((item for item in rutas if item["id"] == route_id), None)
    if ruta_actual is None or not ruta_actual["desbloqueada"]:
        return redirect(str(request.url_for("aprender.mostrar_aprender")))

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


@aprender_router.get(
    "/aprender/leccion/{lesson_id}",
    name="aprender.leccion",
)
async def leccion(request: Request, lesson_id: str):
    if "usuario" not in request.session:
        return redirect(str(request.url_for("auth.login")))

    lesson = RutaModel.obtener_leccion(lesson_id)
    if lesson is None:
        return redirect(str(request.url_for("aprender.mostrar_aprender")))
    for _question, options in lesson["questions"]:
        random.shuffle(options)
    route_id = f"{lesson['unit_id']:02d}"
    route = next(
        (
            item
            for item in RutaModel.obtener_rutas(
                request.session.get("progreso", {})
            )
            if item["id"] == route_id
        ),
        None,
    )
    if route is None or not route["desbloqueada"]:
        return redirect(str(request.url_for("aprender.mostrar_aprender")))

    lessons = RutaModel.obtener_lecciones()
    index = next(i for i, item in enumerate(lessons) if item["id"] == lesson_id)
    previous_activity = (
        request.session.get("progreso", {}).get(lessons[index - 1]["id"], {})
        if index > 0
        else True
    )
    previous_completed = (
        previous_activity.get("completada", False)
        if isinstance(previous_activity, dict)
        else bool(previous_activity)
    )
    if (
        index > 0
        and lessons[index - 1]["unit_id"] == lesson["unit_id"]
        and not previous_completed
    ):
        return redirect(
            str(request.url_for("aprender.ruta", route_id=route_id))
        )
    stored_result = request.session.pop("lesson_result", None)
    resultado = None
    if (
        isinstance(stored_result, dict)
        and stored_result.get("lesson_id") == lesson_id
    ):
        resultado = {
            "score": stored_result["score"],
            "total": stored_result["total"],
            "results": stored_result["results"],
            "answers": stored_result["answers"],
            "completada": stored_result["completada"],
            "next_lesson": (
                RutaModel.obtener_leccion(stored_result["next_lesson_id"])
                if stored_result["next_lesson_id"]
                else None
            ),
            "next_route_id": stored_result["next_route_id"],
        }
    return render_template(
        request,
        "leccion.html",
        lesson=lesson,
        material=RutaModel.obtener_material_leccion(lesson_id),
        resultado=resultado,
    )


@aprender_router.post(
    "/aprender/leccion/{lesson_id}/completar",
    name="aprender.completar_leccion",
)
async def completar_leccion(request: Request, lesson_id: str):
    if "usuario" not in request.session:
        return redirect(str(request.url_for("auth.login")))

    lesson = RutaModel.obtener_leccion(lesson_id)
    if lesson is None:
        return redirect(str(request.url_for("aprender.mostrar_aprender")))
    route_id = f"{lesson['unit_id']:02d}"
    route = next(
        (
            item
            for item in RutaModel.obtener_rutas(
                request.session.get("progreso", {})
            )
            if item["id"] == route_id
        ),
        None,
    )
    if route is None or not route["desbloqueada"]:
        return redirect(str(request.url_for("aprender.mostrar_aprender")))

    form = await request.form()
    answers = [
        form.get(f"respuesta_{number}", "") for number in range(1, 4)
    ]
    results = [
        answer == correct
        for answer, correct in zip(answers, lesson["answers"])
    ]
    score, total = sum(results), len(lesson["answers"])
    progreso = request.session.setdefault("progreso", {})
    progreso[lesson_id] = {
        "completada": score == total,
        "intentada": True,
        "puntuacion": score,
        "total": total,
    }
    progress_repository.save_activity(
        request.session["usuario"].get("id_persona"),
        lesson_id,
        progreso[lesson_id],
    )
    request.session["progreso"] = progreso
    next_lesson = next(
        (
            item
            for item in RutaModel.obtener_lecciones()
            if item["unit_id"] == lesson["unit_id"]
            and item["numero"] > lesson["numero"]
            and score == total
            and not (
                request.session.get("progreso", {})
                .get(item["id"], {})
                .get("completada", False)
                if isinstance(
                    request.session.get("progreso", {}).get(item["id"], {}),
                    dict,
                )
                else request.session.get("progreso", {}).get(item["id"], False)
            )
        ),
        None,
    )
    next_route_id = None
    if score == total and next_lesson is None:
        puzzle_activity = request.session.get("progreso", {}).get(
            "unidad_02_puzzle", {}
        )
        puzzle_completed = (
            puzzle_activity.get("completada", False)
            if isinstance(puzzle_activity, dict)
            else bool(puzzle_activity)
        )
        if lesson["unit_id"] == 2 and not puzzle_completed:
            next_route_id = "02"
        elif lesson["unit_id"] < 4:
            next_route_id = f"{lesson['unit_id'] + 1:02d}"

    request.session["lesson_result"] = {
        "lesson_id": lesson_id,
        "score": score,
        "total": total,
        "results": results,
        "answers": answers,
        "completada": score == total,
        "next_lesson_id": next_lesson["id"] if next_lesson else None,
        "next_route_id": next_route_id,
    }
    return redirect(
        str(request.url_for("aprender.leccion", lesson_id=lesson_id)),
        status_code=303,
    )
