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

## Recuperacion de contrasena

Para Gmail, activa la verificacion en dos pasos y crea una contrasena de
aplicacion desde la seguridad de tu cuenta de Google. No uses la contrasena
normal de Gmail ni la compartas en el repositorio.

Desde la carpeta `Nivora`, crea tu archivo local de configuracion:

```powershell
Copy-Item .env.example .env
```

Completa `NIVORA_SMTP_USERNAME` con tu direccion Gmail y `NIVORA_SMTP_PASSWORD`
con la contrasena de aplicacion de 16 caracteres, sin espacios. Configura
`NIVORA_SMTP_FROM` con esa misma direccion. El archivo `.env` esta excluido de
Git. Reinicia Flask despues de editarlo.
El enlace vence despues de una hora; puedes cambiarlo con
`NIVORA_PASSWORD_RESET_TTL` (segundos). Sin SMTP, en modo debug se muestra un
enlace de prueba en la pantalla.

Para abrir la aplicación desde otro dispositivo en la misma red, configura
`NIVORA_HOST=0.0.0.0` y `NIVORA_PUBLIC_URL` con la IP local del equipo que ejecuta
Flask y el puerto, por ejemplo `http://192.168.1.20:5000`. Ambos dispositivos
deben estar en la misma red y el firewall debe permitir ese puerto.