from flask import Blueprint, render_template, redirect, url_for, session
from models.ruta_model import RutaModel

aprender_bp = Blueprint('aprender', __name__)


@aprender_bp.route('/aprender')
def mostrar_aprender():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    rutas = RutaModel.obtener_rutas()

    return render_template(
        'aprender.html',
        rutas=rutas,
        usuario=session['usuario']['nombre']
    )