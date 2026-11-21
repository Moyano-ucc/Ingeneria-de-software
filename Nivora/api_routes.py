"""HTTP API routes for lesson lookup and evaluation."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from models.ruta_model import RutaModel


api_router = APIRouter()


class Evaluation(BaseModel):
    answers: list[str] = Field(min_length=1, max_length=3)


@api_router.get("/api/health", tags=["Sistema"], name="api.health")
def health():
    return {"status": "ok"}


@api_router.get("/api/lecciones", tags=["Lecciones"], name="api.list_lessons")
def list_lessons():
    return {
        "lecciones": [
            {
                "id": lesson["id"],
                "titulo": lesson["titulo"],
                "unidad": lesson["unit_id"],
                "descripcion": lesson["descripcion"],
            }
            for lesson in RutaModel.obtener_lecciones()
        ]
    }


@api_router.get(
    "/api/lecciones/{lesson_id}",
    tags=["Lecciones"],
    name="api.get_lesson",
)
def get_lesson(lesson_id: str):
    lesson = RutaModel.obtener_leccion(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    return lesson


@api_router.post(
    "/api/lecciones/{lesson_id}/evaluar",
    tags=["Lecciones"],
    name="api.evaluate_lesson",
)
def evaluate_lesson(lesson_id: str, evaluation: Evaluation):
    lesson = RutaModel.obtener_leccion(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    if len(evaluation.answers) != len(lesson["answers"]):
        raise HTTPException(
            status_code=400,
            detail="Debes enviar todas las respuestas",
        )
    score = sum(
        answer == correct
        for answer, correct in zip(evaluation.answers, lesson["answers"])
    )
    return {
        "leccion": lesson_id,
        "puntuacion": score,
        "total": len(lesson["answers"]),
        "completada": score == len(lesson["answers"]),
    }
