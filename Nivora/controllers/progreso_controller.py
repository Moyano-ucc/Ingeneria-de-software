from flask import Blueprint, render_template, redirect, url_for, session
from models.progreso_model import ProgresoModel

progreso_bp = Blueprint('progreso', __name__)

@progreso_bp.route('/progreso')
def mostrar_progreso():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    progreso = ProgresoModel.obtener_progreso(
        session['usuario'].get('id_persona'), session.get('progreso', {})
    )

    return render_template(
        'progreso.html',
        usuario=session['usuario'],
        progreso=progreso
    )