import time

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from repositories.progress_repository import ProgressRepository
from security import csrf_protected
from services.auth_service import EMAIL_PATTERN, AuthService
from services.email_service import EmailService, reset_code_email
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



RESET_EMAIL_KEY = "reset_email"
RESET_SENT_AT_KEY = "reset_code_sent_at"
RESET_FEEDBACK_KEY = "reset_feedback"
CODE_SENT_GENERIC_MESSAGE = (
    "Si el correo está registrado en Nivora, te enviamos un código de 6 dígitos. "
    "Revisa tu bandeja de entrada y la carpeta de spam."
)
CODE_TOO_SOON_MESSAGE = (
    "Ya te enviamos un código hace un momento. Revisa tu correo o espera un "
    "minuto para pedir otro."
)
EMAIL_NOT_CONFIGURED_MESSAGE = (
    "El envío de correos no está configurado en este servidor, así que no "
    "pudimos enviarte el código. Avisa al administrador de Nivora."
)
EMAIL_FAILED_MESSAGE = (
    "No pudimos enviar el correo en este momento. Inténtalo de nuevo en unos "
    "minutos."
)


def _is_dev(request: Request) -> bool:
    return bool(request.app.debug or request.app.state.testing)


async def _send_reset_code(request: Request, email: str, name: str, change: bool):
    """Create a 6-digit code and e-mail it.

    Returns ``(status, dev_code)``. ``status`` is ``"sent"``, ``"unknown_user"``,
    ``"too_soon"``, ``"not_configured"`` or ``"failed"``. ``dev_code`` is only
    filled in debug/testing mode when the e-mail could not be sent, so the flow
    can be tried locally without SMTP.
    """
    config = request.app.state.settings
    sent_at = request.session.get(RESET_SENT_AT_KEY, 0)
    if (
        request.session.get(RESET_EMAIL_KEY) == email
        and time.time() - sent_at < config.PASSWORD_RESET_RESEND_SECONDS
    ):
        return "too_soon", None

    mailer = EmailService(config)
    if mailer.missing_settings() and not _is_dev(request):
        mailer.send(email, "", "")  # logs which variables are missing
        return "not_configured", None

    code, user = auth_service.create_reset_code(email, config.PASSWORD_RESET_TOKEN_TTL)
    if not code:
        return "unknown_user", None

    subject, text, html = reset_code_email(
        name or user["nombre"], code, config.PASSWORD_RESET_TOKEN_TTL, change
    )
    result = await run_in_threadpool(mailer.send, email, subject, text, html)
    if result.sent:
        return "sent", None
    status = "not_configured" if result.error == "not_configured" else "failed"
    return status, (code if _is_dev(request) else None)


def _go_to_code_form(request: Request, email: str, message: str, dev_code=None):
    request.session[RESET_EMAIL_KEY] = email
    request.session[RESET_SENT_AT_KEY] = time.time()
    request.session[RESET_FEEDBACK_KEY] = {"mensaje": message, "dev_code": dev_code}
    return redirect(request.url_for("auth.verificar_codigo"), status_code=303)


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

    status, dev_code = await _send_reset_code(request, email, "", change=False)
    # A missing account gets the same answer as a sent code, so the form
    # cannot be used to discover which addresses are registered.
    if status in {"sent", "unknown_user"}:
        return _go_to_code_form(request, email, CODE_SENT_GENERIC_MESSAGE)
    if status == "too_soon":
        request.session[RESET_FEEDBACK_KEY] = {"mensaje": CODE_TOO_SOON_MESSAGE}
        return redirect(request.url_for("auth.verificar_codigo"), status_code=303)
    message = EMAIL_NOT_CONFIGURED_MESSAGE if status == "not_configured" else EMAIL_FAILED_MESSAGE
    if dev_code:
        return _go_to_code_form(request, email, message, dev_code)
    return render_template(
        request,
        "recuperar_contrasena.html",
        status_code=503,
        email=email,
        mensaje=message,
        mensaje_ok=False,
    )


@auth_router.post("/ajustes/cambiar-contrasena", name="auth.cambiar_contrasena")
async def cambiar_contrasena(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return redirect(request.url_for("auth.login"))

    email = usuario.get("email", "")
    status, dev_code = await _send_reset_code(
        request, email, usuario.get("nombre", ""), change=True
    )
    if status == "sent":
        return _go_to_code_form(
            request,
            email,
            f"Te enviamos un código de 6 dígitos a {email}. Revisa también la carpeta de spam.",
        )
    if status == "too_soon":
        request.session[RESET_FEEDBACK_KEY] = {"mensaje": CODE_TOO_SOON_MESSAGE}
        return redirect(request.url_for("auth.verificar_codigo"), status_code=303)
    if status == "unknown_user":
        message = "No encontramos tu cuenta. Cierra sesión y vuelve a iniciarla."
    elif status == "not_configured":
        message = EMAIL_NOT_CONFIGURED_MESSAGE
    else:
        message = EMAIL_FAILED_MESSAGE
    if dev_code:
        return _go_to_code_form(request, email, message, dev_code)
    request.session["password_change_feedback"] = {"mensaje": message, "ok": False}
    return redirect(request.url_for("auth.ajustes"), status_code=303)


def _code_form(request: Request, email: str, status_code=200, **context):
    feedback = request.session.pop(RESET_FEEDBACK_KEY, None)
    return render_template(
        request,
        "verificar_codigo.html",
        status_code=status_code,
        email=email,
        feedback=feedback,
        field_errors=context.pop("field_errors", {}),
        **context,
    )


@auth_router.api_route(
    "/verificar-codigo",
    methods=["GET", "POST"],
    name="auth.verificar_codigo",
)
async def verificar_codigo(request: Request):
    email = request.session.get(RESET_EMAIL_KEY)
    if not email:
        return redirect(request.url_for("auth.recuperar_contrasena"))

    if request.method == "GET":
        return _code_form(request, email)

    form = await request.form()
    code = "".join(str(form.get("codigo", "")).split())
    password = form.get("password", "")
    confirmation = form.get("confirmacion", "")
    if not (len(code) == 6 and code.isdigit()):
        return _code_form(
            request, email, 400,
            field_errors={"codigo": "Escribe los 6 dígitos que llegaron a tu correo"},
        )
    if not auth_service.password_is_strong(password):
        return _code_form(
            request, email, 400,
            field_errors={"password": "Usa al menos 8 caracteres, con letras y números"},
        )
    if password != confirmation:
        return _code_form(
            request, email, 400,
            field_errors={
                "password": "Las contraseñas no coinciden",
                "confirmacion": "Las contraseñas no coinciden",
            },
        )

    result = auth_service.reset_password_with_code(email, code, password)
    if result == "invalid":
        return _code_form(
            request, email, 400,
            field_errors={"codigo": "El código no es correcto. Revísalo e inténtalo de nuevo."},
        )
    if result == "expired":
        return _code_form(
            request, email, 400,
            codigo_vencido=True,
            field_errors={
                "codigo": "Este código venció, ya se usó o superó los intentos permitidos. "
                "Pide uno nuevo."
            },
        )
    request.session.pop(RESET_EMAIL_KEY, None)
    request.session.pop(RESET_SENT_AT_KEY, None)
    return render_template(
        request,
        "verificar_codigo.html",
        completado=True,
        sesion_iniciada="usuario" in request.session,
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
