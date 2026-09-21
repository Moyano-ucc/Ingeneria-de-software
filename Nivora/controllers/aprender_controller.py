from flask import Blueprint, render_template, redirect, url_for, session, request
from models.ruta_model import RutaModel
from services.auth_service import AuthService

aprender_bp = Blueprint('aprender', __name__)
auth_service = AuthService()


@aprender_bp.route('/aprender')
def mostrar_aprender():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    rutas = RutaModel.obtener_rutas(session.get('progreso', {}))

    return render_template(
        'aprender.html',
        rutas=rutas,
        usuario=session['usuario']['nombre']
    )


@aprender_bp.route('/aprender/leccion/variables')
def leccion_variables():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    lesson = RutaModel.obtener_leccion('variables')
    return render_template('leccion.html', lesson=lesson, resultado=None)


@aprender_bp.route('/aprender/ruta/<route_id>')
def ruta(route_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    if route_id != '01':
        return redirect(url_for('aprender.mostrar_aprender'))
    actividades = session.get('progreso', {})
    actividades = {
        lesson_id: activity if isinstance(activity, dict) else {'completada': bool(activity)}
        for lesson_id, activity in actividades.items()
    }
    return render_template(
        'ruta.html',
        ruta_id=route_id,
        lecciones=RutaModel.LESSONS,
        actividades=actividades
    )


@aprender_bp.route('/aprender/leccion/<lesson_id>', methods=['GET'])
def leccion(lesson_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))
    lesson = RutaModel.obtener_leccion(lesson_id)
    if lesson is None:
        return redirect(url_for('aprender.mostrar_aprender'))
    lessons = RutaModel.LESSONS
    index = next(i for i, item in enumerate(lessons) if item['id'] == lesson_id)
    previous_activity = session.get('progreso', {}).get(lessons[index - 1]['id'], {}) if index > 0 else True
    previous_completed = (
        previous_activity.get('completada', False)
        if isinstance(previous_activity, dict)
        else bool(previous_activity)
    )
    previous_attempt = (
        previous_activity.get('intentada', False)
        if isinstance(previous_activity, dict)
        else False
    )
    if index > 0 and not previous_completed and not previous_attempt:
        return redirect(url_for('aprender.ruta', route_id='01'))
    return render_template('leccion.html', lesson=lesson, resultado=None)


@aprender_bp.route('/aprender/leccion/<lesson_id>/completar', methods=['POST'])
def completar_leccion(lesson_id):
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    lesson = RutaModel.obtener_leccion(lesson_id)
    if lesson is None:
        return redirect(url_for('aprender.mostrar_aprender'))
    answers = [request.form.get(f'respuesta_{number}', '') for number in range(1, 4)]
    results = [answer == correct for answer, correct in zip(answers, lesson['answers'])]
    score, total = sum(results), len(lesson['answers'])
    progreso = session.setdefault('progreso', {})
    progreso[lesson_id] = {
        'completada': score == total,
        'intentada': True,
        'puntuacion': score,
        'total': total,
    }
    session.modified = True
    next_lesson = next(
        (
            item for item in RutaModel.LESSONS
            if item['numero'] > lesson['numero']
            and not (
                session.get('progreso', {}).get(item['id'], {}).get('completada', False)
                if isinstance(session.get('progreso', {}).get(item['id'], {}), dict)
                else session.get('progreso', {}).get(item['id'], False)
            )
        ),
        None,
    )
    return render_template('leccion.html', lesson=lesson, resultado={
        'score': score, 'total': total, 'results': results, 'answers': answers,
        'completada': score == total, 'next_lesson': next_lesson
    })