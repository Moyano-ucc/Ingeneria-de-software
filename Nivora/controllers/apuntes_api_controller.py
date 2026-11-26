"""REST API for the student's personal notes («Mis apuntes»).

It uses every HTTP method on one resource, with path and query parameters:

    GET    /api/apuntes?leccion=variables   list (200)
    POST   /api/apuntes                     create (201 + Location)
    GET    /api/apuntes/{apunte_id}         read one (200 / 404)
    PUT    /api/apuntes/{apunte_id}         replace it completely (200 / 404)
    PATCH  /api/apuntes/{apunte_id}         change some fields (200 / 404)
    DELETE /api/apuntes/{apunte_id}         delete (204 / 404)

Authentication is the same session cookie as the web pages (401 without it),
so the endpoints can be tried from Swagger (/docs) after logging in. The
cookie is SameSite=Lax and the body must be JSON, so another site cannot
trigger these requests on the student's behalf.

Dependencies (current user and repository) are injected with ``Depends``;
tests replace the repository through ``app.dependency_overrides``.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response, status
from pydantic import BaseModel, Field, StringConstraints, model_validator

from models.ruta_model import RutaModel
from repositories.apunte_repository import ApunteRepository


router = APIRouter(prefix="/api/apuntes", tags=["Apuntes"])

ContenidoTexto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
ApunteId = Annotated[int, Path(ge=1, description="Identificador del apunte")]


class ApunteEntrada(BaseModel):
    """Body for POST and PUT: every field is required (PUT replaces everything)."""

    leccion: str = Field(description="Código de la lección, por ejemplo «variables»")
    contenido: ContenidoTexto
    destacado: bool = False


class ApunteCambios(BaseModel):
    """Body for PATCH: only the fields that change."""

    leccion: str | None = None
    contenido: ContenidoTexto | None = None
    destacado: bool | None = None

    @model_validator(mode="after")
    def at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("Envía al menos un campo para modificar")
        return self


class ApunteSalida(BaseModel):
    id: int
    leccion: str
    contenido: str
    destacado: bool
    creado: float
    actualizado: float


def usuario_actual(request: Request) -> dict:
    usuario = request.session.get("usuario")
    if not usuario or not usuario.get("id_persona"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inicia sesión para usar tus apuntes")
    return usuario


def obtener_repositorio() -> ApunteRepository:
    return ApunteRepository()


Usuario = Annotated[dict, Depends(usuario_actual)]
Repositorio = Annotated[ApunteRepository, Depends(obtener_repositorio)]
NOT_FOUND = "Apunte no encontrado"


def _lesson_must_exist(leccion):
    if leccion is not None and RutaModel.obtener_leccion(leccion) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"La lección «{leccion}» no existe")


@router.get("", response_model=list[ApunteSalida], name="api.apuntes.listar")
def listar_apuntes(
    usuario: Usuario,
    repositorio: Repositorio,
    leccion: Annotated[str | None, Query(description="Filtra por lección")] = None,
):
    return repositorio.list(usuario["id_persona"], leccion)


@router.post(
    "",
    response_model=ApunteSalida,
    status_code=status.HTTP_201_CREATED,
    name="api.apuntes.crear",
)
def crear_apunte(apunte: ApunteEntrada, usuario: Usuario, repositorio: Repositorio, response: Response):
    _lesson_must_exist(apunte.leccion)
    creado = repositorio.create(
        usuario["id_persona"], apunte.leccion, apunte.contenido, apunte.destacado
    )
    response.headers["Location"] = f"/api/apuntes/{creado['id']}"
    return creado


@router.get("/{apunte_id}", response_model=ApunteSalida, name="api.apuntes.obtener")
def obtener_apunte(apunte_id: ApunteId, usuario: Usuario, repositorio: Repositorio):
    apunte = repositorio.get(usuario["id_persona"], apunte_id)
    if apunte is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return apunte


@router.put("/{apunte_id}", response_model=ApunteSalida, name="api.apuntes.reemplazar")
def reemplazar_apunte(
    apunte_id: ApunteId, apunte: ApunteEntrada, usuario: Usuario, repositorio: Repositorio
):
    _lesson_must_exist(apunte.leccion)
    actualizado = repositorio.update(
        usuario["id_persona"],
        apunte_id,
        leccion=apunte.leccion,
        contenido=apunte.contenido,
        destacado=apunte.destacado,
    )
    if actualizado is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return actualizado


@router.patch("/{apunte_id}", response_model=ApunteSalida, name="api.apuntes.modificar")
def modificar_apunte(
    apunte_id: ApunteId, cambios: ApunteCambios, usuario: Usuario, repositorio: Repositorio
):
    fields = cambios.model_dump(exclude_unset=True)
    for key, value in fields.items():
        if value is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"«{key}» no puede ser nulo")
    _lesson_must_exist(fields.get("leccion"))
    actualizado = repositorio.update(usuario["id_persona"], apunte_id, **fields)
    if actualizado is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return actualizado


@router.delete(
    "/{apunte_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    name="api.apuntes.eliminar",
)
def eliminar_apunte(apunte_id: ApunteId, usuario: Usuario, repositorio: Repositorio):
    if not repositorio.delete(usuario["id_persona"], apunte_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
