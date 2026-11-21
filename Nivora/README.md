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

## Recuperación de contraseña

Para Gmail, activa la verificación en dos pasos y crea una contraseña de
aplicación. Desde la carpeta `Nivora`, copia `.env.example` a `.env` y completa
`NIVORA_SMTP_USERNAME`, `NIVORA_SMTP_PASSWORD` y `NIVORA_SMTP_FROM`. No subas
credenciales al repositorio. Reinicia Uvicorn al editar el archivo.

El enlace vence después de una hora; puedes cambiarlo con
`NIVORA_PASSWORD_RESET_TTL` (segundos). Sin SMTP, en modo de desarrollo se
muestra un enlace de prueba en pantalla. Para abrir el enlace en la misma
computadora, mantén Uvicorn ejecutándose y configura
`NIVORA_PUBLIC_URL=http://127.0.0.1:8000` en `.env` si el host del enlace no
coincide con la dirección de la aplicación. `127.0.0.1` solo funciona en esa
computadora; no uses `0.0.0.0` como dirección del enlace.

Para abrir la aplicación desde otro dispositivo en la red local, configura
`NIVORA_HOST=0.0.0.0` y `NIVORA_PUBLIC_URL` con la IP del equipo que ejecuta
FastAPI y el puerto, por ejemplo `http://192.168.1.20:8000`.
