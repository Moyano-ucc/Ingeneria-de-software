import smtplib
from email.message import EmailMessage

from flask import Blueprint, current_app, render_template, request, redirect, url_for, session
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


@auth_bp.route('/recuperar-contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'GET':
        email = session.get('usuario', {}).get('email', '')
        return render_template('recuperar_contrasena.html', email=email)

    email = request.form.get('email', '').strip().lower()
    token = auth_service.create_password_reset(
        email, current_app.config['PASSWORD_RESET_TOKEN_TTL']
    )
    reset_link = None
    message = 'Si el correo está registrado, recibirás instrucciones para recuperar tu cuenta.'

    if token:
        reset_path = url_for('auth.restablecer_contrasena', token=token)
        public_base_url = current_app.config.get('PUBLIC_BASE_URL')
        link = (
            f"{public_base_url.rstrip('/')}{reset_path}"
            if public_base_url
            else url_for('auth.restablecer_contrasena', token=token, _external=True)
        )
        smtp_host = current_app.config.get('SMTP_HOST')
        if smtp_host:
            email_message = EmailMessage()
            email_message['Subject'] = 'Recupera tu contraseña de Nivora'
            email_message['From'] = current_app.config['SMTP_FROM']
            email_message['To'] = email
            email_message.set_content(
                f'Usa este enlace para cambiar tu contraseña. Es válido durante una hora:\n\n{link}'
            )
            try:
                with smtplib.SMTP(
                    smtp_host, current_app.config['SMTP_PORT'], timeout=10
                ) as smtp:
                    if current_app.config['SMTP_USE_TLS']:
                        smtp.starttls()
                    username = current_app.config.get('SMTP_USERNAME')
                    if username:
                        smtp.login(username, current_app.config.get('SMTP_PASSWORD', ''))
                    smtp.send_message(email_message)
            except (OSError, smtplib.SMTPException):
                current_app.logger.exception('No se pudo enviar el correo de recuperación')
                if current_app.debug or current_app.testing:
                    reset_link = link
        elif current_app.debug or current_app.testing:
            reset_link = link
        else:
            current_app.logger.error('Configura NIVORA_SMTP_HOST para habilitar recuperación por correo')

    return render_template(
        'recuperar_contrasena.html', mensaje=message, reset_link=reset_link
    )


@auth_bp.route('/restablecer-contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirmation = request.form.get('confirmacion', '')
        if len(password) < 8:
            return render_template(
                'restablecer_contrasena.html', token=token,
                mensaje='La contraseña debe tener al menos 8 caracteres',
            ), 400
        if password != confirmation:
            return render_template(
                'restablecer_contrasena.html', token=token,
                mensaje='Las contraseñas no coinciden',
            ), 400
        if not auth_service.reset_password(token, password):
            return render_template(
                'restablecer_contrasena.html', token=token,
                mensaje='El enlace venció o ya fue utilizado. Solicita uno nuevo.',
            ), 400
        return render_template(
            'restablecer_contrasena.html',
            mensaje='Contraseña actualizada. Ya puedes iniciar sesión.',
            completado=True,
        )

    return render_template('restablecer_contrasena.html', token=token)


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