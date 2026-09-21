# Nivora

Aplicacion Flask para aprender Python.

## Desarrollo

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:NIVORA_SECRET_KEY = "clave-local-de-desarrollo"
flask --app app run --debug
```

## Pruebas

```powershell
pytest -q
```

## Produccion

Configura `NIVORA_SECRET_KEY`, `NIVORA_DATABASE_PATH` y `NIVORA_COOKIE_SECURE=1`.
Ejecuta `deploy.sh` en un entorno Linux con Gunicorn. No actives `FLASK_DEBUG` en produccion.