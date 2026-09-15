from flask import Blueprint, render_template, redirect, url_for, session

practica_bp = Blueprint('practica', __name__)

@practica_bp.route('/practica')
def mostrar_practica():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    return render_template('practica.html')