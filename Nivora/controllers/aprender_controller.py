import json

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request,
)

from models.ruta_model import RutaModel
from repositories.progress_repository import ProgressRepository
from services.auth_service import AuthService


aprender_bp = Blueprint("aprender", __name__)

auth_service = AuthService()
progress_repository = ProgressRepository()


def actividad_completada(activity):
    """Comprueba si una actividad está completada."""
    if isinstance(activity, dict):
        return bool(activity.get("completada"))
    return bool(activity)


def actividad_intentada(activity):
    """Comprueba si una actividad ya fue intentada."""
    if isinstance(activity, dict):
        return bool(activity.get("intentada"))
    return False


def obtener_progreso():
    """Obtiene el progreso actual de la sesión."""
    return session.setdefault("progreso", {})


def normalizar_actividades(actividades):
    """Normaliza el progreso para las plantillas."""
    normalizadas = {}

    for activity_id, activity in actividades.items():
        if isinstance(activity, dict):
            normalizadas[activity_id] = activity
        else:
            normalizadas[activity_id] = {
                "completada": bool(activity),
                "intentada": bool(activity),
                "puntuacion": 0,
                "total": 0,
            }

    return normalizadas


def guardar_actividad(activity_id, nueva_actividad):
    """Guarda el último intento sin borrar una finalización anterior."""
    progreso = obtener_progreso()
    anterior = progreso.get(activity_id, {})
    ya_completada = actividad_completada(anterior)

    actividad = {
        "completada": ya_completada or nueva_actividad["completada"],
        "intentada": True,
        "puntuacion": nueva_actividad["puntuacion"],
        "total": nueva_actividad["total"],
    }

    progreso[activity_id] = actividad
    session["progreso"] = progreso
    session.modified = True

    usuario = session.get("usuario", {})
    id_persona = usuario.get("id_persona")

    if id_persona is not None:
        progress_repository.save_activity(
            id_persona,
            activity_id,
            actividad,
        )

    return actividad


def obtener_siguiente_leccion(lesson, actividades):
    """Busca la siguiente lección pendiente de la misma unidad."""
    lecciones_unidad = [
        item
        for item in RutaModel.obtener_lecciones()
        if item["unit_id"] == lesson["unit_id"]
    ]

    return next(
        (
            item
            for item in lecciones_unidad
            if item["numero"] > lesson["numero"]
            and not actividad_completada(
                actividades.get(item["id"], {})
            )
        ),
        None,
    )


def acceso_permitido(lesson, actividades):
    """Permite repasar e impide saltarse lecciones nuevas."""
    lecciones_unidad = [
        item
        for item in RutaModel.obtener_lecciones()
        if item["unit_id"] == lesson["unit_id"]
    ]

    index = next(
        (
            i
            for i, item in enumerate(lecciones_unidad)
            if item["id"] == lesson["id"]
        ),
        None,
    )

    if index is None:
        return False

    if index == 0:
        return True

    actividad_actual = actividades.get(lesson["id"], {})

    if (
        actividad_intentada(actividad_actual)
        or actividad_completada(actividad_actual)
    ):
        return True

    actividad_anterior = actividades.get(
        lecciones_unidad[index - 1]["id"],
        {},
    )

    return actividad_completada(actividad_anterior)


@aprender_bp.route("/aprender")
def mostrar_aprender():
    """Muestra las unidades y el progreso del usuario."""
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    rutas = RutaModel.obtener_rutas(obtener_progreso())

    return render_template(
        "aprender.html",
        rutas=rutas,
        usuario=session["usuario"]["nombre"],
    )


@aprender_bp.route("/aprender/leccion/variables")
def leccion_variables():
    """Conserva la ruta antigua de variables."""
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    return redirect(
        url_for("aprender.leccion", lesson_id="variables")
    )


@aprender_bp.route(
    "/aprender/ruta/<route_id>",
    methods=["GET", "POST"],
)
def ruta(route_id):
    """Muestra una unidad o el rompecabezas de la Unidad 2."""
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    if route_id not in ("01", "02"):
        return redirect(url_for("aprender.mostrar_aprender"))

    actividades = obtener_progreso()

    if route_id == "02":
        if not RutaModel.unidad_dos_desbloqueada(actividades):
            return redirect(url_for("aprender.mostrar_aprender"))

        es_rompecabezas = (
            request.args.get("actividad") == "rompecabezas"
            or request.method == "POST"
        )

        if es_rompecabezas:
            resultado = None
            selected_ids = []

            if request.method == "POST":
                try:
                    selected_ids = json.loads(
                        request.form.get("sequence", "[]")
                    )
                except (TypeError, json.JSONDecodeError):
                    selected_ids = []

                valid_ids = {
                    piece["id"]
                    for piece in RutaModel.PUZZLE_PIECES
                }

                valid_sequence = (
                    isinstance(selected_ids, list)
                    and len(selected_ids) == len(valid_ids)
                    and all(
                        isinstance(piece_id, str)
                        for piece_id in selected_ids
                    )
                    and set(selected_ids) == valid_ids
                )

                completada = (
                    valid_sequence
                    and selected_ids == RutaModel.PUZZLE_SOLUTION
                )

                guardar_actividad(
                    "unidad_02_puzzle",
                    {
                        "completada": completada,
                        "puntuacion": int(completada),
                        "total": 1,
                    },
                )

                resultado = (
                    "correcto" if completada else "incorrecto"
                )

            return render_template(
                "unidad_dos.html",
                pieces=RutaModel.PUZZLE_PIECES,
                selected_ids=selected_ids,
                resultado=resultado,
            )

    lecciones = [
        lesson
        for lesson in RutaModel.obtener_lecciones()
        if lesson["unit_id"] == int(route_id)
    ]

    return render_template(
        "ruta.html",
        ruta_id=route_id,
        lecciones=lecciones,
        actividades=normalizar_actividades(actividades),
    )


@aprender_bp.route(
    "/aprender/leccion/<lesson_id>",
    methods=["GET"],
)
def leccion(lesson_id):
    """Muestra la teoría y el cuestionario."""
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    lesson = RutaModel.obtener_leccion(lesson_id)

    if lesson is None:
        return redirect(url_for("aprender.mostrar_aprender"))

    actividades = obtener_progreso()

    if (
        lesson["unit_id"] == 2
        and not RutaModel.unidad_dos_desbloqueada(actividades)
    ):
        return redirect(url_for("aprender.mostrar_aprender"))

    if not acceso_permitido(lesson, actividades):
        return redirect(
            url_for(
                "aprender.ruta",
                route_id=f"{lesson['unit_id']:02d}",
            )
        )

    return render_template(
        "leccion.html",
        lesson=lesson,
        resultado=None,
        respuestas_seleccionadas={},
    )


@aprender_bp.route(
    "/aprender/leccion/<lesson_id>/completar",
    methods=["POST"],
)
def completar_leccion(lesson_id):
    """Evalúa las respuestas y conserva el progreso anterior."""
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    lesson = RutaModel.obtener_leccion(lesson_id)

    if lesson is None:
        return redirect(url_for("aprender.mostrar_aprender"))

    actividades = obtener_progreso()

    if (
        lesson["unit_id"] == 2
        and not RutaModel.unidad_dos_desbloqueada(actividades)
    ):
        return redirect(url_for("aprender.mostrar_aprender"))

    if not acceso_permitido(lesson, actividades):
        return redirect(
            url_for(
                "aprender.ruta",
                route_id=f"{lesson['unit_id']:02d}",
            )
        )

    correct_answers = lesson["answers"]

    answers = [
        request.form.get(f"respuesta_{number}", "")
        for number in range(1, len(correct_answers) + 1)
    ]

    results = [
        answer == correct
        for answer, correct in zip(answers, correct_answers)
    ]

    score = sum(results)
    total = len(correct_answers)

    actividad_actual = guardar_actividad(
        lesson_id,
        {
            "completada": total > 0 and score == total,
            "puntuacion": score,
            "total": total,
        },
    )

    actividades = obtener_progreso()
    siguiente_leccion = obtener_siguiente_leccion(
        lesson,
        actividades,
    )

    detalle_respuestas = []

    for index, (answer, correct, is_correct) in enumerate(
        zip(answers, correct_answers, results),
        start=1,
    ):
        question = (
            lesson["questions"][index - 1][0]
            if index - 1 < len(lesson["questions"])
            else f"Pregunta {index}"
        )

        options = (
            lesson["questions"][index - 1][1]
            if index - 1 < len(lesson["questions"])
            else []
        )

        respuesta_usuario = next(
            (
                label
                for value, label in options
                if value == answer
            ),
            answer or "Sin respuesta",
        )

        respuesta_correcta = next(
            (
                label
                for value, label in options
                if value == correct
            ),
            correct,
        )

        detalle_respuestas.append({
            "numero": index,
            "question": question,
            "respuesta_usuario": respuesta_usuario,
            "respuesta_correcta": respuesta_correcta,
            "correcta": is_correct,
        })

    respuestas_seleccionadas = {
        f"respuesta_{number}": answer
        for number, answer in enumerate(answers, start=1)
    }

    return render_template(
        "leccion.html",
        lesson=lesson,
        resultado={
            "score": score,
            "total": total,
            "results": results,
            "detalle_respuestas": detalle_respuestas,
            "answers": answers,
            "completada": actividad_actual["completada"],
            "next_lesson": siguiente_leccion,
        },
        respuestas_seleccionadas=respuestas_seleccionadas,
    )
