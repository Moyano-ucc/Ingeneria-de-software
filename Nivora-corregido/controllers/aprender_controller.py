from flask import Blueprint, render_template
from models.ruta_model import RutaModel

aprender_bp = Blueprint('aprender', __name__)


@aprender_bp.route('/aprender')
def mostrar_aprender():
    rutas = RutaModel.obtener_rutas()

    return render_template(
        'aprender.html',
        rutas=rutas,
        usuario='estudiante'
    )