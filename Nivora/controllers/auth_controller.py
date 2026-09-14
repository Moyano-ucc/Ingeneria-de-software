from flask import Blueprint, render_template, request, redirect, url_for
from models.usuario_model import UsuarioModel

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if UsuarioModel.autenticar(email, password):
            return redirect(url_for('aprender.mostrar_aprender'))

        return render_template(
            'login.html',
            mensaje='Correo o contraseña incorrectos'
        )

    return render_template('login.html')


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        registrado, mensaje = UsuarioModel.registrar(email, password)

        if registrado:
            return redirect(url_for('auth.login'))

        return render_template(
            'registro.html',
            mensaje=mensaje
        )

    return render_template('registro.html')