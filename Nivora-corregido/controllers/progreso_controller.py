from flask import Blueprint, render_template

progreso_bp = Blueprint('progreso', __name__)


@progreso_bp.route('/progreso')
def mostrar_progreso():
    return render_template('progreso.html')