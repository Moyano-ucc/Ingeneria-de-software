from flask import Blueprint, render_template, request, redirect, url_for, session
from models.usuario_model import UsuarioModel

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        usuario = UsuarioModel.autenticar(email, password)

        if usuario:
            session['usuario'] = usuario
            return redirect(url_for('aprender.mostrar_aprender'))

        return render_template(
            'login.html',
            mensaje='Correo o contraseña incorrectos'
        )

    return render_template('login.html')


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        registrado, mensaje = UsuarioModel.registrar(nombre, email, password)

        if registrado:
            session['usuario'] = {'nombre': nombre, 'email': email}
            return redirect(url_for('aprender.mostrar_aprender'))

        return render_template(
            'registro.html',
            mensaje=mensaje
        )

    return render_template('registro.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@auth_bp.route('/ajustes')
def ajustes():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    return render_template('ajustes.html', usuario=session['usuario'])