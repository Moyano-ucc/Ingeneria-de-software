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
variable. Las prácticas de la primera unidad (dificultad fácil) se resuelven con
bloques que construyen el código, o escribiéndolo si el estudiante lo prefiere;
las unidades siguientes combinan retos para ordenar bloques, completar código
con fichas y emparejar conceptos. Cada reto muestra objetivo, pasos, pistas
progresivas y una explicación del error sin revelar la solución.

Las respuestas del último intento de cada quiz se guardan en la base de datos:
se conservan al ir al reto práctico y volver. «Repetir quiz» inicia un intento
nuevo y las lecciones completadas pueden repasarse sin perder el progreso.
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
- `services/`: lógica de negocio (`auth_service`, `email_service` para los
  correos y `practica_service` para evaluar retos con retroalimentación).
- `models/`: dominio y contenido (`ruta_model`, `progreso_model`,
  `contenido_lecciones` con la teoría y `ejercicios_practica` con los retos).
- `repositories/`: acceso a SQLite (usuarios, tokens y progreso).
- `templates/` y `static/`: interfaz HTML, estilos, imágenes y JavaScript.
- `tests/`: pruebas automatizadas (`conftest.py` aísla la base de datos en
  cada prueba).

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
   - `NIVORA_SMTP_HOST`, `NIVORA_SMTP_USERNAME`, `NIVORA_SMTP_PASSWORD` para los correos.
5. Monta `/home/data` como carpeta persistente. Para producción con múltiples
   instancias, usa Azure SQL o PostgreSQL en lugar de SQLite.

## Arquitectura y patrones

Nivora aplica separación de responsabilidades con controladores, servicios,
modelos y repositorios:

- **Factory:** `create_app()` configura y construye la aplicación FastAPI.
- **Repository:** `UserRepository` y `ProgressRepository` aíslan el acceso SQLite.
- **Service:** `AuthService` contiene registro, autenticación y recuperación.
- **Facade:** `UsuarioModel` ofrece una interfaz simple sobre autenticación.
- **Strategy:** `recommend_level()` selecciona la recomendación según las
  respuestas recibidas, y `services/practica_service.py` aplica una estrategia
  de evaluación distinta para código y para cada tipo de rompecabezas.
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

Ambos flujos envían por correo un **código de 6 dígitos**. El estudiante lo
escribe en `/verificar-codigo` junto con su contraseña nueva:

- **Recuperar contraseña** (`/recuperar-contrasena`): para quien no puede
  iniciar sesión. Por seguridad, la respuesta es la misma exista o no la cuenta.
- **Cambiar contraseña** (`Ajustes`): envía el código al correo de la cuenta
  con la sesión iniciada.

Reglas de seguridad: el código vence a los 15 minutos
(`NIVORA_PASSWORD_RESET_TTL`, en segundos), sirve una sola vez, se bloquea tras
5 intentos fallidos, pedir uno nuevo invalida el anterior y hay que esperar 60
segundos entre envíos. En la base de datos solo se guarda un hash del código.

Configuración necesaria:

| Variable | Ejemplo |
| --- | --- |
| `NIVORA_SMTP_HOST` | `smtp.gmail.com` |
| `NIVORA_SMTP_PORT` | `587` (STARTTLS) o `465` (SSL) |
| `NIVORA_SMTP_USERNAME` | cuenta que envía los correos |
| `NIVORA_SMTP_PASSWORD` | contraseña de aplicación de Gmail |
| `NIVORA_SMTP_FROM` | `Nivora <cuenta@gmail.com>` (opcional: por defecto usa el usuario) |

Dónde configurarlas:

- **GitHub Codespaces (recomendado):** créalas una sola vez en
  https://github.com/settings/codespaces → *Codespaces secrets*, con acceso a
  este repositorio, y reinicia el Codespace. Así funcionan en cualquier
  Codespace nuevo.
- **Local:** copia `.env.example` a `.env` dentro de `Nivora` y reinicia Uvicorn.

Nunca subas credenciales al repositorio. Si falta configuración o el servidor
SMTP rechaza el envío, Nivora lo indica en pantalla y registra el motivo en la
consola; nunca muestra un envío exitoso que no ocurrió. En modo
desarrollo/pruebas aparece además un código de prueba en pantalla.

## GitHub Codespaces y proxies

Las redirecciones de Nivora son relativas, por lo que el navegador mantiene el
dominio desde el que se accede (`https://<codespace>-8000.app.github.dev`,
`http://127.0.0.1:8000`, Azure, etc.). En Codespaces ejecuta:

```bash
cd Nivora
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

y abre el puerto 8000 desde la pestaña **Puertos**.

Para abrir la aplicación desde otro dispositivo en la red local, configura
`NIVORA_HOST=0.0.0.0` y entra con la IP del equipo, por ejemplo
`http://192.168.1.20:8000`.
