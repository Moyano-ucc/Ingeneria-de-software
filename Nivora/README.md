# Nivora

Aplicación FastAPI para aprender Python, con interfaz HTML y API REST.

## Desarrollo

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:NIVORA_SECRET_KEY = "clave-local-de-desarrollo"
uvicorn app:app --reload --reload-include "*.html" --reload-include "*.css" --reload-include "*.js" --reload-include "*.png" --reload-include "*.jpg" --reload-include "*.jpeg" --reload-include "*.svg" --reload-include "*.webp"
```

La aplicación queda en `http://127.0.0.1:8000`; Swagger está en `/docs`.
Ejecuta estos comandos desde la carpeta `Nivora`. Uvicorn reiniciará la
aplicación al cambiar Python, plantillas, estilos, scripts o imágenes. Si el
navegador conserva una versión anterior, fuerza la actualización con `Ctrl+F5`.
La sesión caduca tras 15 minutos sin solicitudes al servidor. Algunos
navegadores restauran ventanas y cookies al reabrirse, así que para cerrar la
sesión inmediatamente usa el botón **Cerrar sesión** antes de cerrar el navegador.

El registro solicita confirmar la contraseña y exige al menos ocho caracteres
con letras y números. Cada pregunta del quiz ofrece cuatro opciones en orden
variable. Las prácticas de la primera unidad conservan el editor de código y
las unidades siguientes combinan retos para ordenar bloques, completar código
con fichas y emparejar conceptos.
Las animaciones de la portada se activan al cargar, incluso si el sistema
prefiere reducir el movimiento.

## Pruebas

```powershell
pytest -q
```

## Estructura del proyecto

- `app.py`: configura FastAPI, middleware, routers y archivos estáticos.
- `api_routes.py`: endpoints REST documentados por OpenAPI/Swagger.
- `controllers/`: rutas web agrupadas por funcionalidad.
- `services/`, `models/` y `repositories/`: lógica, dominio y persistencia.
- `templates/` y `static/`: interfaz HTML, estilos, imágenes y JavaScript.
- `tests/`: pruebas automatizadas.

## Producción

Configura `NIVORA_SECRET_KEY`, `NIVORA_DATABASE_PATH` y
`NIVORA_COOKIE_SECURE=1`. Ejecuta `deploy.sh` en Linux con Gunicorn y Uvicorn.
No actives `NIVORA_DEBUG` en producción.

## Azure App Service

1. Crea un App Service Linux con Python 3.12.
2. Despliega desde GitHub Actions o Git local.
3. Configura `bash startup.sh` como comando de inicio.
4. Agrega estas variables en **Configuración > Configuración de la aplicación**:
   - `NIVORA_SECRET_KEY`: valor aleatorio largo y privado.
   - `NIVORA_COOKIE_SECURE=1`
   - `NIVORA_DATABASE_PATH=/home/data/nivora.db`
   - `NIVORA_PUBLIC_URL=https://TU-APP.azurewebsites.net`
5. Monta `/home/data` como carpeta persistente. Para producción con múltiples
   instancias, usa Azure SQL o PostgreSQL en lugar de SQLite.

## Arquitectura y patrones

Nivora aplica separación de responsabilidades con controladores, servicios,
modelos y repositorios:

- **Factory:** `create_app()` configura y construye la aplicación FastAPI.
- **Repository:** `UserRepository` y `ProgressRepository` aíslan el acceso SQLite.
- **Service:** `AuthService` contiene registro, autenticación y recuperación.
- **Facade:** `UsuarioModel` ofrece una interfaz simple sobre autenticación.
- **Strategy:** `recommend_level()` y `grade_lesson()` seleccionan el comportamiento
  de recomendación y evaluación según las respuestas recibidas.
- **Template Method:** los controladores comparten el flujo de sesión, validación
  CSRF, evaluación y persistencia.

Los principios SOLID se aplican mediante responsabilidades separadas,
dependencias sustituibles, interfaces pequeñas y acceso a datos aislado.

## API REST

La interfaz web y la API se sirven desde la misma aplicación FastAPI (`app:app`).

- Swagger: `http://127.0.0.1:8000/docs`
- Salud: `GET /api/health`
- Lecciones: `GET /api/lecciones`
- Lección por identificador: `GET /api/lecciones/{lesson_id}`
- Evaluación: `POST /api/lecciones/{lesson_id}/evaluar`

## Recuperación y cambio de contraseña

Ambos flujos envían por correo un enlace de un solo uso (vence según
`NIVORA_PASSWORD_RESET_TTL`, una hora por defecto):

- **Recuperar contraseña** (`/recuperar-contrasena`): para quien no puede
  iniciar sesión. Por seguridad, la respuesta es la misma exista o no la cuenta.
- **Cambiar contraseña** (`Ajustes`): envía el enlace al correo de la cuenta
  con la sesión iniciada.

Configuración necesaria (copia `.env.example` a `.env` dentro de `Nivora` y
reinicia Uvicorn):

| Variable | Ejemplo |
| --- | --- |
| `NIVORA_SMTP_HOST` | `smtp.gmail.com` |
| `NIVORA_SMTP_PORT` | `587` (STARTTLS) o `465` (SSL) |
| `NIVORA_SMTP_USERNAME` | cuenta que envía los correos |
| `NIVORA_SMTP_PASSWORD` | contraseña de aplicación de Gmail |
| `NIVORA_SMTP_FROM` | `Nivora <cuenta@gmail.com>` (opcional: por defecto usa el usuario) |

Si falta configuración o el servidor SMTP rechaza el envío, Nivora lo indica en
pantalla y registra el motivo en la consola; nunca muestra un envío exitoso que
no ocurrió. En modo desarrollo/pruebas aparece además un enlace de prueba.

Los enlaces de los correos usan `NIVORA_PUBLIC_URL` si está definida; si no,
el dominio desde el que se hizo la solicitud (incluido el de Codespaces).

## GitHub Codespaces y proxies

Las redirecciones de Nivora son relativas, por lo que el navegador mantiene el
dominio desde el que se accede (`https://<codespace>-8000.app.github.dev`,
`http://127.0.0.1:8000`, Azure, etc.). En Codespaces ejecuta:

```bash
cd Nivora
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

y abre el puerto 8000 desde la pestaña **Puertos**. No configures
`NIVORA_PUBLIC_URL` con `localhost` ni con una IP local en Codespaces.

Para abrir la aplicación desde otro dispositivo en la red local, configura
`NIVORA_HOST=0.0.0.0` y, si quieres fijar el dominio de los correos,
`NIVORA_PUBLIC_URL` con la IP del equipo, por ejemplo `http://192.168.1.20:8000`.
