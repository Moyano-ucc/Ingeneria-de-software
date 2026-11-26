from datetime import datetime

from fastapi import APIRouter, Request

from models.progreso_model import ProgresoModel
from repositories.certificate_repository import CertificateRepository
from repositories.progress_repository import ProgressRepository
from security import csrf_protected
from views.responses import redirect, render_template


certificado_router = APIRouter(dependencies=csrf_protected, tags=["Páginas: certificado"])
certificate_repository = CertificateRepository()
progress_repository = ProgressRepository()
MONTHS = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def fecha_larga(timestamp):
    date = datetime.fromtimestamp(timestamp)
    return f"{date.day} de {MONTHS[date.month - 1]} de {date.year}"


@certificado_router.get("/certificado", name="certificado.mostrar")
async def mostrar_certificado(request: Request):
    usuario = request.session.get("usuario")
    if not usuario:
        return redirect(request.url_for("auth.login"))

    # The database is the source of truth for completion.
    user_id = usuario.get("id_persona")
    actividades = (
        progress_repository.find_by_user(user_id)
        if user_id
        else request.session.get("progreso", {})
    )
    progreso = ProgresoModel.obtener_progreso(user_id, actividades)
    if not progreso["curso_completado"] or not user_id:
        return render_template(
            request,
            "certificado.html",
            status_code=403,
            bloqueado=True,
            progreso=progreso,
        )

    certificado = certificate_repository.issue(user_id)
    return render_template(
        request,
        "certificado.html",
        nombre=usuario["nombre"],
        codigo=certificado["codigo"],
        fecha=fecha_larga(certificado["fecha_emision"]),
        unidades=[ruta["nombre"] for ruta in progreso["rutas"]],
        lecciones=progreso["general"]["total"],
        url_verificacion=request.url_for(
            "certificado.verificar", codigo=certificado["codigo"]
        ).path,
    )


@certificado_router.get(
    "/certificado/verificar/{codigo}", name="certificado.verificar"
)
async def verificar_certificado(request: Request, codigo: str):
    certificado = certificate_repository.find_by_code(codigo)
    return render_template(
        request,
        "certificado_verificar.html",
        status_code=200 if certificado else 404,
        certificado=certificado,
        codigo=codigo,
        fecha=fecha_larga(certificado["fecha_emision"]) if certificado else None,
    )
