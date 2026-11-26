"""Web pages for registration, initial level, login, logout and settings.

Each route has one function per HTTP method (GET shows the page, POST
processes the form and redirects with 303: the Post/Redirect/Get pattern).
Password recovery lives in ``password_controller.py``.
"""

from fastapi import APIRouter, Request

from repositories.progress_repository import ProgressRepository
from security import csrf_protected
from services.auth_service import AuthService
from views.responses import redirect, render_template


auth_router = APIRouter(dependencies=csrf_protected, tags=["Páginas: cuenta"])
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


def _start_session(request: Request, usuario: dict):
    request.session.clear()
    request.session["usuario"] = usuario
    request.session["progreso"] = progress_repository.find_by_user(usuario["id_persona"])


@auth_router.get("/login", name="auth.login")
async def login_page(request: Request):
    if "usuario" in request.session:
        return redirect(request.url_for("aprender.mostrar_aprender"))
    return render_template(
        request, "login.html", field_errors=_consume_field_errors(request, "login")
    )


@auth_router.post("/login", name="auth.login.enviar")
async def login_submit(request: Request):
    form = await request.form()
    usuario = auth_service.authenticate(form.get("email", ""), form.get("password", ""))
    if usuario:
        _start_session(request, usuario)
        return redirect(request.url_for("aprender.mostrar_aprender"), status_code=303)

    message = "Correo o contraseña incorrectos"
    return _redirect_with_field_errors(request, "login", {"email": message, "password": message})


@auth_router.get("/registro", name="auth.registro")
async def registro_page(request: Request):
    usuario = request.session.get("usuario")
    if usuario:
        destination = "aprender.mostrar_aprender" if usuario.get("recomendacion") else "auth.nivel"
        return redirect(request.url_for(destination))
    return render_template(
        request, "registro.html", field_errors=_consume_field_errors(request, "registro")
    )


@auth_router.post("/registro", name="auth.registro.enviar")
async def registro_submit(request: Request):
    form = await request.form()
    email = form.get("email", "")
    password = form.get("password", "")
    registrado, mensaje = auth_service.register(
        form.get("nombre", ""), email, password, form.get("confirmacion", "")
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
        _start_session(request, usuario)
        return redirect(request.url_for("auth.nivel"), status_code=303)

    if "nombre" in mensaje:
        fields = {"nombre": mensaje}
    elif "correo" in mensaje:
        fields = {"email": mensaje}
    elif "no coinciden" in mensaje:
        fields = {"password": mensaje, "confirmacion": mensaje}
    else:
        fields = {"password": mensaje}
    return _redirect_with_field_errors(request, "registro", fields)


@auth_router.get("/nivel", name="auth.nivel")
async def nivel_page(request: Request):
    if "usuario" not in request.session:
        return redirect(request.url_for("auth.registro"))
    if request.session["usuario"].get("recomendacion"):
        return redirect(request.url_for("aprender.mostrar_aprender"))
    return render_template(request, "nivel.html")


@auth_router.post("/nivel", name="auth.nivel.enviar")
async def nivel_submit(request: Request):
    if "usuario" not in request.session:
        return redirect(request.url_for("auth.registro"), status_code=303)

    form = await request.form()
    if form.get("nivel_inicial") == "no_se_nada":
        recomendacion = auth_service.recommend_level(["", "", ""])
    else:
        quiz_answers = [form.get(f"pregunta_{number}", "") for number in range(1, 4)]
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
    return redirect(request.url_for("aprender.mostrar_aprender"), status_code=303)


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
