import smtplib
from email.message import EmailMessage

from fastapi import APIRouter, Request

from repositories.progress_repository import ProgressRepository
from security import csrf_protected
from services.auth_service import AuthService
from views.responses import redirect, render_template


auth_router = APIRouter(dependencies=csrf_protected)
auth_service = AuthService()
progress_repository = ProgressRepository()
FORM_FEEDBACK_KEY = "form_feedback"


def _consume_field_errors(request: Request, form_name: str) -> dict:
    feedback = request.session.pop(FORM_FEEDBACK_KEY, None)
    if not isinstance(feedback, dict) or feedback.get("form") != form_name:
        return {}
    fields = feedback.get("fields", {})
    return fields if isinstance(fields, dict) else {}


def _redirect_with_field_errors(request: Request, form_name: str, fields: dict):
    request.session[FORM_FEEDBACK_KEY] = {"form": form_name, "fields": fields}
    route_name = "auth.login" if form_name == "login" else "auth.registro"
    return redirect(request.url_for(route_name), status_code=303)


@auth_router.api_route("/login", methods=["GET", "POST"], name="auth.login")
async def login(request: Request):
    if request.method == "GET":
        if "usuario" in request.session:
            return redirect(request.url_for("aprender.mostrar_aprender"))
        return render_template(
            request,
            "login.html",
            field_errors=_consume_field_errors(request, "login"),
        )

    if request.method == "POST":
        form = await request.form()
        email = form.get("email", "")
        password = form.get("password", "")
        usuario = auth_service.authenticate(email, password)

        if usuario:
            request.session.clear()
            request.session["usuario"] = usuario
            request.session["progreso"] = progress_repository.find_by_user(
                usuario["id_persona"]
            )
            return redirect(
                request.url_for("aprender.mostrar_aprender"),
                status_code=303,
            )

        message = "Correo o contraseña incorrectos"
        return _redirect_with_field_errors(
            request,
            "login",
            {"email": message, "password": message},
        )



@auth_router.api_route(
    "/recuperar-contrasena",
    methods=["GET", "POST"],
    name="auth.recuperar_contrasena",
)
async def recuperar_contrasena(request: Request):
    if request.method == "GET":
        email = request.session.get("usuario", {}).get("email", "")
        return render_template(request, "recuperar_contrasena.html", email=email)

    form = await request.form()
    email = str(form.get("email", "")).strip().lower()
    config = request.app.state.settings
    token = auth_service.create_password_reset(
        email, config.PASSWORD_RESET_TOKEN_TTL
    )
    reset_link = None
    message = (
        "Si el correo está registrado, recibirás instrucciones para recuperar tu cuenta."
    )

    if token:
        reset_url = request.url_for("auth.restablecer_contrasena", token=token)
        public_base_url = config.PUBLIC_BASE_URL
        link = (
            f"{public_base_url.rstrip('/')}{reset_url.path}"
            if public_base_url
            else str(reset_url)
        )
        smtp_host = config.SMTP_HOST
        if smtp_host:
            email_message = EmailMessage()
            email_message["Subject"] = "Recupera tu contraseña de Nivora"
            email_message["From"] = config.SMTP_FROM
            email_message["To"] = email
            email_message.set_content(
                "Usa este enlace para cambiar tu contraseña. "
                f"Es válido durante una hora:\n\n{link}"
            )
            try:
                with smtplib.SMTP(
                    smtp_host, config.SMTP_PORT, timeout=10
                ) as smtp:
                    if config.SMTP_USE_TLS:
                        smtp.starttls()
                    if config.SMTP_USERNAME:
                        smtp.login(
                            config.SMTP_USERNAME,
                            config.SMTP_PASSWORD or "",
                        )
                    smtp.send_message(email_message)
            except (OSError, smtplib.SMTPException):
                request.app.state.logger.exception(
                    "No se pudo enviar el correo de recuperación"
                )
                if request.app.debug or request.app.state.testing:
                    reset_link = link
        elif request.app.debug or request.app.state.testing:
            reset_link = link
        else:
            request.app.state.logger.error(
                "Configura NIVORA_SMTP_HOST para habilitar recuperación por correo"
            )

    return render_template(
        request,
        "recuperar_contrasena.html",
        mensaje=message,
        reset_link=reset_link,
    )


@auth_router.api_route(
    "/restablecer-contrasena/{token}",
    methods=["GET", "POST"],
    name="auth.restablecer_contrasena",
)
async def restablecer_contrasena(request: Request, token: str):
    if request.method == "POST":
        form = await request.form()
        password = form.get("password", "")
        confirmation = form.get("confirmacion", "")
        if not auth_service.password_is_strong(password):
            return render_template(
                request,
                "restablecer_contrasena.html",
                status_code=400,
                token=token,
                field_errors={
                    "password": "Usa al menos 8 caracteres, con letras y números"
                },
            )
        if password != confirmation:
            return render_template(
                request,
                "restablecer_contrasena.html",
                status_code=400,
                token=token,
                field_errors={
                    "password": "Las contraseñas no coinciden",
                    "confirmacion": "Las contraseñas no coinciden",
                },
            )
        if not auth_service.reset_password(token, password):
            return render_template(
                request,
                "restablecer_contrasena.html",
                status_code=400,
                token=token,
                mensaje="El enlace venció o ya fue utilizado. Solicita uno nuevo.",
                field_errors={},
            )
        return render_template(
            request,
            "restablecer_contrasena.html",
            mensaje="Contraseña actualizada. Ya puedes iniciar sesión.",
            completado=True,
        )

    return render_template(
        request,
        "restablecer_contrasena.html",
        token=token,
        field_errors={},
    )


@auth_router.api_route("/registro", methods=["GET", "POST"], name="auth.registro")
async def registro(request: Request):
    if request.method == "GET":
        usuario = request.session.get("usuario")
        if usuario:
            destination = (
                "aprender.mostrar_aprender"
                if usuario.get("recomendacion")
                else "auth.nivel"
            )
            return redirect(request.url_for(destination))
        return render_template(
            request,
            "registro.html",
            field_errors=_consume_field_errors(request, "registro"),
        )

    if request.method == "POST":
        form = await request.form()
        nombre = form.get("nombre", "")
        email = form.get("email", "")
        password = form.get("password", "")
        confirmation = form.get("confirmacion", "")
        registrado, mensaje = auth_service.register(
            nombre,
            email,
            password,
            confirmation,
        )

        if registrado:
            usuario = auth_service.authenticate(email, password)
            if usuario is None:
                return render_template(
                    request,
                    "registro.html",
                    status_code=500,
                    mensaje="La cuenta se creó, pero no se pudo iniciar la sesión",
                )
            request.session.clear()
            request.session["usuario"] = usuario
            request.session["progreso"] = progress_repository.find_by_user(
                usuario["id_persona"]
            )
            return redirect(
                request.url_for("auth.nivel"),
                status_code=303,
            )

        if "nombre" in mensaje:
            fields = {"nombre": mensaje}
        elif "correo" in mensaje or "correo electrónico" in mensaje:
            fields = {"email": mensaje}
        elif "no coinciden" in mensaje:
            fields = {"password": mensaje, "confirmacion": mensaje}
        else:
            fields = {"password": mensaje}
        return _redirect_with_field_errors(request, "registro", fields)


@auth_router.api_route("/nivel", methods=["GET", "POST"], name="auth.nivel")
async def nivel(request: Request):
    if "usuario" not in request.session:
        return redirect(request.url_for("auth.registro"))
    if (
        request.method == "GET"
        and request.session["usuario"].get("recomendacion")
    ):
        return redirect(request.url_for("aprender.mostrar_aprender"))

    if request.method == "POST":
        form = await request.form()
        if form.get("nivel_inicial") == "no_se_nada":
            recomendacion = auth_service.recommend_level(["", "", ""])
        else:
            quiz_answers = [
                form.get(f"pregunta_{number}", "") for number in range(1, 4)
            ]
            if any(not answer for answer in quiz_answers):
                return render_template(
                    request,
                    "nivel.html",
                    status_code=400,
                    mensaje="Responde las tres preguntas para continuar",
                )
            recomendacion = auth_service.recommend_level(quiz_answers)

        usuario = dict(request.session["usuario"])
        usuario["nivel"] = recomendacion["codigo"]
        usuario["recomendacion"] = recomendacion
        request.session["usuario"] = usuario
        return redirect(request.url_for("aprender.mostrar_aprender"))

    return render_template(request, "nivel.html")


@auth_router.post("/logout", name="auth.logout")
async def logout(request: Request):
    request.session.clear()
    return redirect(request.url_for("home"), status_code=303)


@auth_router.get("/ajustes", name="auth.ajustes")
async def ajustes(request: Request):
    if "usuario" not in request.session:
        return redirect(request.url_for("auth.login"))

    return render_template(
        request,
        "ajustes.html",
        usuario=request.session["usuario"],
    )
