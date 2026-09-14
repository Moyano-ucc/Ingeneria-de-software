from flask import Blueprint, render_template

practica_bp = Blueprint('practica', __name__)

@practica_bp.route('/practica')
def mostrar_practica():
    return render_template('practica.html')