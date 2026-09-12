from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.usuario_model import UsuarioModel

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        exito, mensaje = UsuarioModel.registrar(email, password)
        if exito:
            return redirect(url_for('aprender.mostrar_aprender'))
        return render_template('registro.html', error=mensaje)
    return render_template('registro.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if UsuarioModel.autenticar(email, password):
            # Redirección a la sección Aprender
            return redirect(url_for('aprender.mostrar_aprender'))
        return render_template('login.html', error="Credenciales inválidas")
    return render_template('login.html')