from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from repositories.progress_repository import ProgressRepository
from security import csrf_protected
from services.auth_service import EMAIL_PATTERN, AuthService
from services.email_service import EmailService, password_email
from views.responses import public_url, redirect, render_template


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



RECOVERY_GENERIC_MESSAGE = (
    "Si el correo está registrado en Nivora, te enviamos un enlace para crear "
    "una contraseña nueva. Revisa tu bandeja de entrada y la carpeta de spam."
)
EMAIL_NOT_CONFIGURED_MESSAGE = (
    "El envío de correos no está configurado en este servidor, así que no "
    "pudimos enviarte el enlace. Avisa al administrador de Nivora."
)
EMAIL_FAILED_MESSAGE = (
    "No pudimos enviar el correo en este momento. Inténtalo de nuevo en unos "
    "minutos."
)


async def _send_password_link(request: Request, email: str, name: str, change: bool):
    """Create a reset token and e-mail the link.

    Returns ``(status, dev_link)`` where ``status`` is ``"sent"``,
    ``"unknown_user"``, ``"not_configured"`` or ``"failed"``. ``dev_link`` is
    only filled in debug/testing mode when the e-mail could not be sent, so
    the flow can still be tested locally without SMTP.
    """
    config = request.app.state.settings
    mailer = EmailService(config)
    token = auth_service.create_password_reset(email, config.PASSWORD_RESET_TOKEN_TTL)
    if not token:
        return "unknown_user", None

    link = public_url(
        request, request.url_for("auth.restablecer_contrasena", token=token)
    )
    subject, text, html = password_email(
        name, link, config.PASSWORD_RESET_TOKEN_TTL, change
    )
    result = await run_in_threadpool(mailer.send, email, subject, text, html)
    if result.sent:
        return "sent", None
    dev_link = link if (request.app.debug or request.app.state.testing) else None
    status = "not_configured" if result.error == "not_configured" else "failed"
    return status, dev_link


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
    if not EMAIL_PATTERN.fullmatch(email):
        return render_template(
            request,
            "recuperar_contrasena.html",
            status_code=400,
            email=email,
            field_errors={"email": "Introduce un correo electrónico válido"},
        )

    status, dev_link = await _send_password_link(request, email, "", change=False)
    # A missing account gets the same answer as a sent e-mail, so the form
    # cannot be used to discover which addresses are registered.
    if status in {"sent", "unknown_user"}:
        message, ok = RECOVERY_GENERIC_MESSAGE, True
    elif status == "not_configured":
        message, ok = EMAIL_NOT_CONFIGURED_MESSAGE, False
    else:
        message, ok = EMAIL_FAILED_MESSAGE, False
    return render_template(
        request,
        "recuperar_contrasena.html",
        status_code=200 if ok else 503,
        email=email,
        mensaje=message,
        mensaje_ok=ok,
        reset_link=dev_link,
    )


@auth_router.post("/ajustes/cambiar-contrasena", name="auth.cambiar_contrasena")
async def cambiar_contrasena(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return redirect(request.url_for("auth.login"))

    email = usuario.get("email", "")
    status, dev_link = await _send_password_link(
        request, email, usuario.get("nombre", ""), change=True
    )
    if status == "sent":
        message, ok = (
            f"Te enviamos un correo a {email} con el enlace para cambiar tu "
            "contraseña. Revisa también la carpeta de spam.",
            True,
        )
    elif status == "unknown_user":
        message, ok = (
            "No encontramos tu cuenta. Cierra sesión y vuelve a iniciarla.",
            False,
        )
    elif status == "not_configured":
        message, ok = EMAIL_NOT_CONFIGURED_MESSAGE, False
    else:
        message, ok = EMAIL_FAILED_MESSAGE, False
    request.session["password_change_feedback"] = {
        "mensaje": message,
        "ok": ok,
        "reset_link": dev_link,
    }
    return redirect(request.url_for("auth.ajustes"), status_code=303)


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
                enlace_invalido=True,
                mensaje="El enlace venció o ya fue utilizado. Solicita uno nuevo.",
            )
        return render_template(
            request,
            "restablecer_contrasena.html",
            mensaje="Contraseña actualizada. Ya puedes iniciar sesión.",
            completado=True,
        )

    if not auth_service.reset_token_is_valid(token):
        return render_template(
            request,
            "restablecer_contrasena.html",
            status_code=400,
            enlace_invalido=True,
            mensaje="El enlace venció o ya fue utilizado. Solicita uno nuevo.",
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
        feedback=request.session.pop("password_change_feedback", None),
    )
