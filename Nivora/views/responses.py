from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import pass_context
from starlette.routing import NoMatchFound
from starlette.templating import Jinja2Templates

from security import csrf_token


TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


@pass_context
def template_url_for(context, name: str, **path_params) -> str:
    if name == "static" and "filename" in path_params:
        path_params["path"] = path_params.pop("filename")
    request = context["request"]
    try:
        url = request.url_for(name, **path_params)
    except NoMatchFound:
        url = request.url_for(name).include_query_params(**path_params)
    return url.path + (f"?{url.query}" if url.query else "")


TEMPLATES.env.globals["url_for"] = template_url_for


def render_template(
    request: Request,
    template_name: str,
    status_code: int = 200,
    **context,
) -> HTMLResponse:
    token = csrf_token(request)
    template_context = {
        "request": request,
        "session": request.session,
        "csrf_token": lambda: token,
        **context,
    }
    return TEMPLATES.TemplateResponse(
        request=request,
        name=template_name,
        context=template_context,
        status_code=status_code,
    )


def redirect(url: str, status_code: int = 302) -> RedirectResponse:
    return RedirectResponse(url=url, status_code=status_code)


def error_page(request: Request, message: str, status_code: int) -> HTMLResponse:
    return render_template(
        request,
        "error.html",
        status_code=status_code,
        mensaje=message,
    )
