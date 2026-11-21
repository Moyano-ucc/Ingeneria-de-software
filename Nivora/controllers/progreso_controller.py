from fastapi import APIRouter, Request

from models.progreso_model import ProgresoModel
from security import csrf_protected
from views.responses import redirect, render_template


progreso_router = APIRouter(dependencies=csrf_protected)


@progreso_router.get("/progreso", name="progreso.mostrar_progreso")
async def mostrar_progreso(request: Request):
    if "usuario" not in request.session:
        return redirect(str(request.url_for("auth.login")))

    progreso = ProgresoModel.obtener_progreso(
        request.session["usuario"].get("id_persona"),
        request.session.get("progreso", {}),
    )
    return render_template(
        request,
        "progreso.html",
        usuario=request.session["usuario"],
        progreso=progreso,
    )
