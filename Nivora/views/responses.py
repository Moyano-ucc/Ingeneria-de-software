from pathlib import Path
from urllib.parse import urlsplit

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


def relative_url(url) -> str:
    """Return only the path and query of an application URL.

    ``request.url_for`` builds absolute URLs from the ``Host`` header received
    by Uvicorn. Behind a reverse proxy (GitHub Codespaces, Azure, Nginx) that
    header is usually the internal address (``localhost:8000``), so an
    absolute ``Location`` sends the browser to a host it cannot reach. A
    relative ``Location`` is resolved by the browser against the domain it is
    already using, which works locally and behind any proxy.
    """
    parts = urlsplit(str(url))
    path = parts.path or "/"
    return f"{path}?{parts.query}" if parts.query else path


def redirect(url, status_code: int = 302) -> RedirectResponse:
    return RedirectResponse(url=relative_url(url), status_code=status_code)


def public_url(request: Request, url) -> str:
    """Build an absolute URL for links that leave the browser (e-mails).

    Priority: ``NIVORA_PUBLIC_URL`` > proxy headers (``X-Forwarded-Host`` and
    ``X-Forwarded-Proto``, sent by Codespaces and most proxies) > request URL.
    """
    path = relative_url(url)
    configured = getattr(request.app.state.settings, "PUBLIC_BASE_URL", None)
    if configured:
        return f"{configured.rstrip('/')}{path}"
    forwarded_host = request.headers.get("x-forwarded-host", "").split(",")[0].strip()
    if forwarded_host:
        forwarded_proto = (
            request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
            or request.url.scheme
        )
        return f"{forwarded_proto}://{forwarded_host}{path}"
    return f"{request.url.scheme}://{request.url.netloc}{path}"


def error_page(request: Request, message: str, status_code: int) -> HTMLResponse:
    return render_template(
        request,
        "error.html",
        status_code=status_code,
        mensaje=message,
    )
