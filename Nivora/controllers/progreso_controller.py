from flask import Blueprint, render_template, redirect, url_for, session

progreso_bp = Blueprint('progreso', __name__)


@progreso_bp.route('/progreso')
def mostrar_progreso():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    return render_template('progreso.html', usuario=session['usuario'])