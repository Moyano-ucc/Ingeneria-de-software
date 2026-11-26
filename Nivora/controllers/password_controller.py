"""Web pages to recover or change the password with an e-mailed 6-digit code.

Flow: ask for the code (recovery or settings) → the code arrives by e-mail →
/verificar-codigo checks it and saves the new password.
"""

import time

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from security import csrf_protected
from services.auth_service import EMAIL_PATTERN, AuthService
from services.email_service import EmailService, reset_code_email
from views.responses import redirect, render_template


password_router = APIRouter(dependencies=csrf_protected, tags=["Páginas: contraseña"])
auth_service = AuthService()

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


def _too_soon(request: Request):
    request.session[RESET_FEEDBACK_KEY] = {"mensaje": CODE_TOO_SOON_MESSAGE}
    return redirect(request.url_for("auth.verificar_codigo"), status_code=303)


@password_router.get("/recuperar-contrasena", name="auth.recuperar_contrasena")
async def recuperar_page(request: Request):
    email = request.session.get("usuario", {}).get("email", "")
    return render_template(request, "recuperar_contrasena.html", email=email)


@password_router.post("/recuperar-contrasena", name="auth.recuperar_contrasena.enviar")
async def recuperar_submit(request: Request):
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
        return _too_soon(request)
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


@password_router.post("/ajustes/cambiar-contrasena", name="auth.cambiar_contrasena")
async def cambiar_contrasena(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return redirect(request.url_for("auth.login"))

    email = usuario.get("email", "")
    status, dev_code = await _send_reset_code(request, email, usuario.get("nombre", ""), change=True)
    if status == "sent":
        return _go_to_code_form(
            request,
            email,
            f"Te enviamos un código de 6 dígitos a {email}. Revisa también la carpeta de spam.",
        )
    if status == "too_soon":
        return _too_soon(request)
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
    return render_template(
        request,
        "verificar_codigo.html",
        status_code=status_code,
        email=email,
        feedback=request.session.pop(RESET_FEEDBACK_KEY, None),
        field_errors=context.pop("field_errors", {}),
        **context,
    )


@password_router.get("/verificar-codigo", name="auth.verificar_codigo")
async def verificar_page(request: Request):
    email = request.session.get(RESET_EMAIL_KEY)
    if not email:
        return redirect(request.url_for("auth.recuperar_contrasena"))
    return _code_form(request, email)


@password_router.post("/verificar-codigo", name="auth.verificar_codigo.enviar")
async def verificar_submit(request: Request):
    email = request.session.get(RESET_EMAIL_KEY)
    if not email:
        return redirect(request.url_for("auth.recuperar_contrasena"), status_code=303)

    form = await request.form()
    code = "".join(str(form.get("codigo", "")).split())
    password = form.get("password", "")
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
    if password != form.get("confirmacion", ""):
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
