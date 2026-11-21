import secrets

from fastapi import Depends, HTTPException, Request


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if token is None:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


async def validate_csrf(request: Request) -> None:
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            request_size = int(content_length)
        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail="Longitud de solicitud inválida",
            ) from error
        if request_size > request.app.state.max_content_length:
            raise HTTPException(
                status_code=413,
                detail="La solicitud es demasiado grande",
            )

    form = await request.form()
    form_token = form.get("csrf_token")
    expected = request.session.get("csrf_token")
    if (
        not isinstance(form_token, str)
        or not expected
        or not secrets.compare_digest(expected, form_token)
    ):
        raise HTTPException(status_code=400, detail="Token CSRF inválido")


csrf_protected = [Depends(validate_csrf)]
