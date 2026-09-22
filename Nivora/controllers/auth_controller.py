from flask import Blueprint, render_template, request, redirect, url_for, session
from repositories.progress_repository import ProgressRepository
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()
progress_repository = ProgressRepository()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')

        usuario = auth_service.authenticate(email, password)

        if usuario:
            session.clear()
            session['usuario'] = usuario
            session['progreso'] = progress_repository.find_by_user(usuario['id_persona'])
            return redirect(url_for('aprender.mostrar_aprender'))

        return render_template(
            'login.html',
            mensaje='Correo o contraseña incorrectos'
        )

    return render_template('login.html')


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        registrado, mensaje = auth_service.register(nombre, email, password)

        if registrado:
            usuario = auth_service.authenticate(email, password)
            if usuario is None:
                return render_template(
                    'registro.html',
                    mensaje='La cuenta se creó, pero no se pudo iniciar la sesión'
                ), 500
            session.clear()
            session['usuario'] = usuario
            session['progreso'] = progress_repository.find_by_user(usuario['id_persona'])
            return redirect(url_for('auth.nivel'))

        return render_template(
            'registro.html',
            mensaje=mensaje
        )

    return render_template('registro.html')


@auth_bp.route('/nivel', methods=['GET', 'POST'])
def nivel():
    if 'usuario' not in session:
        return redirect(url_for('auth.registro'))

    if request.method == 'POST':
        if request.form.get('nivel_inicial') == 'no_se_nada':
            recomendacion = auth_service.recommend_level(["", "", ""])
        else:
            quiz_answers = [
                request.form.get(f'pregunta_{number}', '')
                for number in range(1, 4)
            ]
            if any(not answer for answer in quiz_answers):
                return render_template(
                    'nivel.html', mensaje='Responde las tres preguntas para continuar'
                ), 400
            recomendacion = auth_service.recommend_level(quiz_answers)

        session['usuario']['nivel'] = recomendacion['codigo']
        session['usuario']['recomendacion'] = recomendacion
        session.modified = True
        return redirect(url_for('aprender.mostrar_aprender'))

    return render_template('nivel.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@auth_bp.route('/ajustes')
def ajustes():
    if 'usuario' not in session:
        return redirect(url_for('auth.login'))

    return render_template('ajustes.html', usuario=session['usuario'])