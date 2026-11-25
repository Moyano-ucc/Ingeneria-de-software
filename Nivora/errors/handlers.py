import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from views.responses import error_page


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, error: StarletteHTTPException):
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=error.status_code,
                content={"detail": error.detail},
                headers=error.headers,
            )
        message = (
            "La página no existe"
            if error.status_code == 404
            else str(error.detail)
        )
        return error_page(request, message, error.status_code)

    @app.exception_handler(Exception)
    async def internal_error(request: Request, error: Exception):
        logging.getLogger("nivora").exception(
            "Error interno al atender %s",
            request.url.path,
            exc_info=error,
        )
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=500,
                content={"detail": "Ocurrió un error interno"},
            )
        return error_page(request, "Ocurrió un error interno", 500)
