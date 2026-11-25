# Plan maestro de pruebas de Nivora

| | |
|---|---|
| Proyecto | Nivora: plataforma web para aprender Python (FastAPI + Jinja2 + SQLite) |
| Rama | `Nivorafinal2` |
| Versión del plan | 1.0, noviembre de 2026 |
| Estado de la suite | 217 casos automáticos aprobados (100 %), cobertura de líneas de la aplicación del 94,1 % |

---

## 1. Introducción

Este documento define **qué** se prueba en Nivora, **cómo**, **cuándo**, **con qué herramientas** y **quién** es responsable. Su objetivo es comprobar de forma organizada que la plataforma cumple sus funciones (registro, lecciones, quizzes, retos, progreso, contraseñas y certificado) y que lo hace de forma segura y con un rendimiento aceptable.

El plan está pensado para **aplicarse de verdad**: cada requisito apunta a pruebas concretas del repositorio (sección 15), la mayoría se ejecuta automáticamente con un solo comando y en cada push mediante integración continua, y lo que no puede automatizarse está descrito como casos manuales con pasos y resultados esperados.

### 1.1 Diagnóstico del estado anterior

Antes de este plan no existía ningún documento de pruebas en ninguna rama del repositorio. Lo único que había era una suite de pytest que había crecido junto al código. Al revisarla críticamente se encontró lo siguiente:

| Hallazgo | Consecuencia | Qué se hizo |
|---|---|---|
| No había plan ni criterios de salida | No se sabía cuándo una versión estaba lista | Este documento (secciones 11 y 13) |
| Pruebas agrupadas por «entrega» y un archivo de 34 pruebas mezcladas (`test_app.py`) | No se distinguía qué era unitario, de integración o de sistema; difícil de mantener | Reorganización en `tests/unit`, `tests/integration`, `tests/system` y `tests/smoke`, con marcadores automáticos por carpeta |
| No había smoke test | Para una verificación rápida había que correr todo | `tests/smoke/` (16 casos, ~1 s) y ejecución separada en la integración continua |
| Ninguna trazabilidad requisito → prueba | No se podía demostrar qué requisito estaba cubierto | Matriz de trazabilidad (sección 15) |
| Seguridad probada solo en un formulario (CSRF en `/login`) | Riesgo de formularios sin protección o páginas accesibles sin sesión | `tests/system/test_seguridad.py`: CSRF en los 9 formularios, 7 páginas protegidas, inyección SQL, XSS, hash de contraseñas y códigos, cabeceras, cookie y errores internos |
| Valores límite de la API sin probar | Cambios en el modelo podían romper los clientes sin que nadie lo notara | Casos 0/1/2/3/4 respuestas en `test_api.py` y en la colección de Postman |
| Ninguna prueba no funcional de rendimiento | Desconocíamos el comportamiento con varios usuarios | Script de k6 y medición preliminar, que **encontró dos defectos** (D-08) |
| Pruebas poco útiles o redundantes | Ruido | Se conservaron (no fallan y documentan comportamiento), pero se señalan en la sección 6.4 |

---

## 2. Alcance

### Dentro del alcance

- Autenticación: registro, nivel inicial, inicio y cierre de sesión, sesiones y acceso a páginas protegidas.
- Aprendizaje: unidades, desbloqueo, lecciones, teoría, quizzes, repetición, repaso y progreso.
- Práctica: editor de código, bloques (nivel fácil), rompecabezas y retroalimentación guiada.
- Contraseñas: recuperación y cambio con código de 6 dígitos enviado por correo.
- Certificado de finalización y su verificación pública.
- API REST (`/api/...`).
- No funcionales: seguridad, rendimiento, confiabilidad (migraciones y concurrencia), compatibilidad y usabilidad (manuales).
- Despliegue detrás de proxy (GitHub Codespaces).

### Fuera del alcance

- Entrega real de correos por Gmail en cada ejecución automática: se simula el servidor SMTP. La entrega real se valida con un caso manual (CP-07).
- Infraestructura de Azure y la carpeta `Azure/`.
- Pruebas con múltiples instancias o bases de datos distintas de SQLite.
- Exactitud pedagógica fina de los textos: la revisa el equipo en la prueba de aceptación, no una herramienta.

---

## 3. Requisitos bajo prueba

Prioridad según el riesgo (sección 12): **A** = alta, **M** = media, **B** = baja.

| ID | Requisito | Prioridad |
|---|---|---|
| RF-01 | Registrar una cuenta con nombre de 2 a 30 caracteres, correo válido y contraseña de al menos 8 caracteres con letras y números | A |
| RF-02 | Iniciar y cerrar sesión; la sesión vence tras 15 minutos sin actividad | A |
| RF-03 | Recomendar un nivel inicial («No sé nada» o mini quiz) | B |
| RF-04 | Las unidades se desbloquean en orden: una unidad se abre al completar todas las lecciones de la anterior | A |
| RF-05 | Cada lección muestra teoría completa (explicación, analogía, ejemplo, líneas, salida, errores, reto) | M |
| RF-06 | El quiz se aprueba con 3 de 3; las respuestas se conservan al salir y volver; «Repetir quiz» inicia un intento nuevo | A |
| RF-07 | Las lecciones completadas se pueden repasar sin perder el progreso | A |
| RF-08 | Los retos evalúan el código sin ejecutarlo, aceptan soluciones equivalentes y explican el error sin revelar la solución; el nivel fácil ofrece bloques | M |
| RF-09 | La página de progreso muestra el avance por unidad y general | M |
| RF-10 | Recuperar y cambiar la contraseña con un código de 6 dígitos (15 minutos, un solo uso, máximo 5 intentos, 60 s entre envíos) | A |
| RF-11 | Certificado al completar las 16 lecciones, con fecha y código fijos y verificación pública | M |
| RF-12 | API REST de lecciones y evaluación | B |
| RNF-01 | Seguridad: CSRF, control de acceso, contraseñas y códigos con hash, sin inyección SQL ni XSS, errores sin detalles internos | A |
| RNF-02 | Funcionar detrás de un proxy (Codespaces) sin redirigir a `localhost` | A |
| RNF-03 | Rendimiento: con 20 usuarios simultáneos, p95 < 500 ms y menos de 1 % de errores | M |
| RNF-04 | Confiabilidad: las migraciones conservan los datos y soportan conexiones concurrentes | A |
| RNF-05 | Usabilidad y compatibilidad: uso en móvil y escritorio, Chrome y Firefox, navegación con teclado | M |

---

## 4. Enfoque de pruebas

### 4.1 Niveles

| Nivel | Qué se prueba en Nivora | Dónde | Casos | Herramienta |
|---|---|---|---|---|
| **Unitarias** | Reglas de `AuthService` con un repositorio falso, evaluación de código y rompecabezas, configuración del correo | `tests/unit/` | 50 | pytest |
| **Integración** | Servicios y repositorios contra un SQLite real: códigos de recuperación, progreso, certificados, migraciones, concurrencia, contenido del curso | `tests/integration/` | 34 | pytest |
| **Sistema** | Flujos completos por HTTP como los haría un usuario: registro → lección → quiz → progreso → certificado; contraseñas; API; seguridad; proxy | `tests/system/` | 117 | pytest + TestClient de FastAPI |
| **Aceptación** | Que Nivora cumpla lo que el equipo espera de una plataforma didáctica | Casos manuales CP (sección 8) y criterios de la sección 13 | 12 | Navegador (opcionalmente grabados con Selenium IDE) |

Además hay 16 casos de **smoke** (`tests/smoke/`). Cada prueba usa su propia base de datos temporal (`tests/conftest.py`), así que **nunca toca `database/nivora.db`** y las pruebas son independientes entre sí.

### 4.2 Tipos

| Tipo | Cómo se aplica |
|---|---|
| **Funcionales** | Casi toda la suite: cada RF tiene pruebas automáticas (sección 15) |
| **No funcionales: seguridad** | `tests/system/test_seguridad.py` (marcador `security`), además de las pruebas de bloqueo de códigos y de anti-enumeración de cuentas |
| **No funcionales: rendimiento** | `qa/k6/carga_basica.js` (sección 7.3) |
| **No funcionales: confiabilidad** | Migraciones con datos antiguos y conexiones concurrentes (`tests/integration/test_repositorios.py`) |
| **No funcionales: usabilidad y compatibilidad** | Casos manuales CP-09 a CP-12 |
| **Smoke** | `python -m pytest -m smoke`: 16 casos en unos 2 segundos; es lo primero que corre la integración continua |
| **Regresión** | La suite completa se ejecuta en cada push. Cada defecto corregido deja una prueba que lo reproduce (sección 14) |
| **Exploratorias** | Sesiones con objetivo y tiempo limitado (sección 9) |

### 4.3 Estrategias

- **Basada en requisitos:** cada requisito de la sección 3 tiene al menos una prueba (matriz en la sección 15).
- **Basada en riesgos:** se probó más a fondo, y con más técnicas, lo que tendría consecuencias graves si fallara: autenticación, progreso, contraseñas y seguridad (sección 12). Por ejemplo, el desbloqueo de unidades tiene tabla de decisión completa, mientras que la recomendación de nivel (riesgo bajo) tiene una sola tabla pequeña.
- **Basada en defectos anteriores:** las zonas donde ya hubo fallos (redirecciones, persistencia del quiz, correos, unidad 2) tienen pruebas de regresión específicas y se revisan primero en cada sesión exploratoria (sección 14).

---

## 5. Técnicas de diseño aplicadas

Estas técnicas no son decorativas: cada tabla corresponde a pruebas parametrizadas que existen en el repositorio.

### 5.1 Partición de equivalencia

| Dato | Clases válidas | Clases inválidas | Prueba |
|---|---|---|---|
| Correo de registro | `ana@example.com`, mayúsculas (se normaliza) | sin `@`, sin dominio de primer nivel, con espacios, vacío | `unit/test_reglas_autenticacion.py::test_email_equivalence_classes` |
| Contraseña | letras y números, letras no ASCII (`ñandú2024`) | solo letras, solo números, vacía, `None` | `test_password_rule`, `system/test_contrasenas.py::test_reset_applies_the_same_password_rule_as_registration` |
| Respuestas del quiz por API | todas correctas | algunas correctas, ninguna correcta | `system/test_api.py::test_evaluation_score_classes` |
| Código del estudiante | solución exacta y equivalentes (espacios, orden de sumandos, otro mensaje de `input`) | vacío, error de sintaxis, comillas, mayúsculas, `==`, operador incorrecto, falta `print` | `unit/test_evaluacion_practica.py` |
| Correo en recuperación | cuenta existente | cuenta inexistente (misma respuesta, sin envío) | `system/test_contrasenas.py::test_unknown_email_gets_the_same_answer_without_sending_anything` |

### 5.2 Análisis de valores límite

| Regla | Valores probados | Prueba |
|---|---|---|
| Nombre: 2 a 30 caracteres | 1, 2, 30, 31 y solo espacios | `test_name_length_boundaries` |
| Contraseña: mínimo 8 | 7 y 8 | `test_password_rule`, `test_reset_applies_the_same_password_rule_as_registration` |
| Quiz: se aprueba con 3/3 | 2/3 y 3/3 | `system/test_aprendizaje.py::test_quiz_completion_boundary` |
| Certificado: 16 lecciones | 0, 15 y 16 | `system/test_certificado.py::test_certificate_requires_every_lesson` |
| Intentos del código: máximo 5 | 4.º intento (aún permite reintentar) y 5.º (bloquea) | `integration/test_repositorios.py::test_reset_code_attempt_limit_boundary` |
| Vencimiento del código | un instante antes, exactamente en el vencimiento y después | `test_reset_code_expiry_boundary` |
| Reenvío del código: 60 s | inmediato (bloqueado) y pasado el tiempo | `test_a_new_code_replaces_the_previous_one_and_resending_is_throttled` |
| Respuestas en la API: de 1 a 3 en el modelo, exactamente 3 en la lección | 0, 1, 2, 3 y 4 | `test_evaluation_answer_count_boundaries` y Postman API-05 a API-09 |

### 5.3 Tablas de decisión

**Acceso a una lección** (`test_lesson_access_decision_table`)

| Sesión | Unidad desbloqueada | Lección anterior completada | Resultado |
|---|---|---|---|
| No | – | – | Redirige a `/login` |
| Sí | No | – | Redirige a `/aprender` |
| Sí | Sí | No | Redirige a la página de la unidad |
| Sí | Sí | Sí, o es la primera lección | Muestra la lección (200) |

**Desbloqueo de unidades** (`test_unit_unlocking_decision_table`)

| Unidades completadas | Unidades abiertas |
|---|---|
| Ninguna | 01 |
| 1 | 01, 02 |
| 1 y 2 | 01 a 03 |
| 1, 2 y 3 | 01 a 04 |
| 2 y 3, pero no la 1 | Solo 01 (esta fila encontró el defecto D-07) |

**Resultado de pedir un código de recuperación** (`system/test_contrasenas.py`)

| SMTP configurado | Cuenta existe | Envío aceptado | Modo | Resultado |
|---|---|---|---|---|
| Sí | Sí | Sí | – | Pantalla del código con mensaje neutro; correo enviado |
| Sí | No | – | – | Mismo mensaje neutro; no se envía nada |
| Sí | Sí | No | Producción | Error 503 «No pudimos enviar el correo» |
| No | – | – | Producción | Error 503 «no está configurado» |
| No | Sí | – | Desarrollo | Se muestra un código de prueba en pantalla |

**Obtención del certificado** (`system/test_certificado.py`)

| Sesión | 16 lecciones completadas en la base de datos | Resultado |
|---|---|---|
| No | – | Redirige a `/login` |
| Sí | No (aunque la sesión diga que sí) | 403 con el progreso actual |
| Sí | Sí | Certificado (se emite una vez y luego se reutiliza) |

### 5.4 Pruebas que se conservan aunque aportan poco

- `smoke/test_smoke.py::test_homepage_enables_animations_even_with_reduced_motion_preference` comprueba un detalle de presentación. Se mantiene como smoke de la portada.
- `system/test_seguridad.py::test_session_cookie_expires_after_fifteen_minutes` lee la configuración en lugar de esperar 15 minutos. Es aceptable: la expiración real la garantiza Starlette.
- Hay solapamiento parcial entre `test_protected_routes_redirect_relatively_to_login` (verifica que la redirección sea relativa) y `test_protected_pages_require_a_session` (verifica el control de acceso). Se mantienen ambas porque cubren riesgos distintos (RNF-02 y RNF-01).

---

## 6. Herramientas

| Herramienta | Uso en Nivora | Estado |
|---|---|---|
| **pytest** + **TestClient** de FastAPI | Unitarias, integración, sistema, smoke y seguridad | En uso: 217 casos |
| **pytest-cov** (opcional) | Medir la cobertura: `pip install pytest-cov` y luego `python -m pytest --cov=.` | Medido: 94,1 % |
| **GitHub Actions** | Smoke y regresión en cada push a `main` y `Nivorafinal2` (`.github/workflows/ci.yml`) | En uso |
| **Postman / Newman** | `qa/postman/Nivora_API.postman_collection.json`: 9 peticiones con aserciones (estado, contenido, tiempo de respuesta) | Lista. Sus peticiones y estados se verificaron contra la aplicación; falta ejecutarla en Postman o Newman |
| **k6** | `qa/k6/carga_basica.js`: 20 usuarios virtuales con umbrales de aceptación | Listo; pendiente de ejecutar con k6 (sección 7.3) |
| **Selenium IDE** | Grabar los casos manuales CP-01, CP-03 y CP-05 para repetirlos en cada entrega | Recomendado; los casos ya tienen pasos listos para grabar |
| **Navegador con DevTools** | Casos manuales y exploratorios, vista móvil y consola sin errores | En uso |
| **MiroFish** | Se mencionó en clase, pero no se evaluó en este trabajo | Pendiente de investigar si aporta algo que no cubran las herramientas anteriores; no se incorpora sin un uso concreto |

---

## 7. Ejecución

### 7.1 Comandos

```bash
cd Nivora
python -m pytest -q                 # suite completa (regresión)
python -m pytest -m smoke -q        # smoke (~2 s)
python -m pytest -m unit -q         # o: integration, system, security
python -m pytest --cov=. -q         # con cobertura (requiere pytest-cov)
```

### 7.2 API con Postman

1. Arranca Nivora: `uvicorn app:app --port 8000`.
2. En Postman, **Import** → `qa/postman/Nivora_API.postman_collection.json`.
3. Ajusta la variable `baseUrl` si hace falta y ejecuta la colección con **Run collection**. Las 9 peticiones deben quedar en verde.
4. Alternativa desde la terminal: `npx newman run qa/postman/Nivora_API.postman_collection.json --env-var baseUrl=http://127.0.0.1:8000`.

### 7.3 Rendimiento con k6

```bash
k6 run qa/k6/carga_basica.js
k6 run -e BASE_URL=https://<codespace>-8000.app.github.dev qa/k6/carga_basica.js
```

El escenario sube a 10 usuarios, se mantiene con 20 (un grupo de clase) y baja; mezcla portada, lista de lecciones, evaluación por API y login. Para aprobar, menos de 1 % de las peticiones deben fallar y el 95 % debe responder en menos de 500 ms.

**Medición preliminar.** k6 no estaba disponible en el entorno de desarrollo, así que se midió el mismo escenario con un generador en Python: 20 usuarios durante 15 s, sin pausas, un solo proceso de Uvicorn en una máquina de 4 núcleos. No sustituye a k6, pero sirvió para encontrar dos defectos:

| Versión | Peticiones/s | p95 | Máximo | Errores |
|---|---|---|---|---|
| Antes de corregir D-08 | ~325 | ~246 ms | 3,5–5 s | 2–12 por ejecución (HTTP 500) |
| Después de corregir D-08 | **822** | **43 ms** | **0,4 s** | **0** |

---

## 8. Casos de prueba manuales (sistema y aceptación)

Cubren lo que una prueba automática no puede comprobar bien: apariencia, servicios externos reales, navegadores e interacción. Se ejecutan antes de cada entrega y se marcan en la tabla de la sección 13.

| ID | Caso | Pasos | Resultado esperado | Req. |
|---|---|---|---|---|
| CP-01 | Registro con requisitos en vivo | Ir a Registrarse; escribir la contraseña `abc`, luego `abcdefg1`; escribir otra confirmación y después la misma | Los requisitos se marcan con ✓ al cumplirse; aparece «Las contraseñas no coinciden» y desaparece al corregir; se llega a «Elige tu nivel» | RF-01 |
| CP-02 | Proxy de Codespaces | En un Codespace, abrir el puerto 8000; iniciar sesión, evaluar un quiz y salir | Nunca aparece `localhost` ni `ERR_CONNECTION_REFUSED` | RNF-02 |
| CP-03 | Recorrido de una lección | Leer la teoría, desplegar «¿qué imprime?», responder mal el quiz, abrir el reto, volver | Las respuestas siguen marcadas; «Repetir quiz» aparece justo debajo del mensaje y muestra el quiz vacío | RF-05, RF-06 |
| CP-04 | Repaso en todas las unidades | Con la unidad completada, pulsar «Repasar» en cada unidad, incluida la 2 | Se abre la lección con el quiz vacío; el progreso no baja | RF-07 |
| CP-05 | Bloques en nivel fácil | En «Crea una variable…», construir `edad = "20"` con fichas, evaluar, corregir con «Limpiar» | Explica que las comillas lo convierten en texto; luego «¡Respuesta correcta!»; «Prefiero escribir el código» permite editar | RF-08 |
| CP-06 | Rompecabezas de la lección 4 de la unidad 2 | Ordenar mal los 8 bloques y comprobar | Indica cuántos bloques están bien y qué línea revisar, sin dar la solución | RF-08 |
| CP-07 | Correo real de recuperación | Con los secretos SMTP configurados: «¿Olvidaste tu contraseña?» → correo → código → contraseña nueva | Llega «XXXXXX es tu código de Nivora» (revisar spam); se cambia la contraseña y se puede iniciar sesión con ella | RF-10 |
| CP-08 | Certificado | Con las 16 lecciones completadas: Tu progreso → «Ver mi certificado» → «Descargar PDF» | El PDF ocupa una sola hoja horizontal con nombre, fecha y código; el enlace de verificación lo confirma | RF-11 |
| CP-09 | Vista móvil | DevTools en modo móvil (360 px): portada, lección, reto con bloques, código de verificación | No hay desplazamiento horizontal; los botones se pueden pulsar | RNF-05 |
| CP-10 | Navegadores | Repetir CP-01, CP-03 y CP-08 en Chrome y Firefox | Mismo comportamiento; la consola no muestra errores | RNF-05 |
| CP-11 | Teclado | Completar el registro y un quiz solo con Tab, Espacio y Enter | Todo es alcanzable; el foco se ve | RNF-05 |
| CP-12 | Aceptación pedagógica | Una persona que no programa sigue la unidad 1 completa | Entiende la teoría sin ayuda externa y completa los retos guiada por las pistas | RF-05, RF-08 |

---

## 9. Pruebas exploratorias

Sesiones de 30 minutos, cada una con un objetivo («charter»). Quien explora anota lo que hizo, lo que encontró y las ideas para nuevas pruebas. Cada hallazgo se registra en la sección 14 y, si es un defecto, se escribe primero la prueba que lo reproduce.

| Sesión | Objetivo |
|---|---|
| EX-1 | Romper el progreso: repetir lecciones en distinto orden, usar dos pestañas, volver atrás con el navegador |
| EX-2 | Abusar de los códigos de recuperación: muchos intentos, reenvíos seguidos, dos cuentas, cambiar de correo a mitad del proceso |
| EX-3 | Entradas extrañas en los retos: código muy largo, emojis, tabulaciones, otro idioma, pegar código de otra lección |
| EX-4 | Sesión vencida: dejar una lección abierta más de 15 minutos y enviar el quiz |
| EX-5 | Zonas con defectos anteriores: redirecciones (E01), respuestas del quiz (E02) y unidad 2 (D-05) |

---

## 10. Roles y responsabilidades

| Rol | Responsabilidades |
|---|---|
| Desarrollador/a de cada funcionalidad | Escribir las pruebas unitarias, de integración y de sistema junto con el código; no subir cambios con pruebas fallando |
| Responsable de QA del equipo (rotativo por entrega) | Mantener este plan y la matriz; ejecutar los casos manuales, las sesiones exploratorias y k6; registrar los defectos y las métricas |
| Revisor/a del cambio | Comprobar que cada defecto corregido trae su prueba de regresión y que la integración continua está en verde |
| Docente o usuario de aceptación | Validar CP-12 y los criterios de aceptación |

---

## 11. Cronograma

| Momento | Qué se ejecuta | Responsable |
|---|---|---|
| Mientras se programa | Las pruebas del área que se modifica (`pytest tests/system/test_aprendizaje.py`, etc.) | Desarrollador/a |
| Cada push a `main` o `Nivorafinal2` | Smoke y luego la suite completa en GitHub Actions | Automático |
| Antes de cada entrega | Casos manuales CP-01 a CP-11, colección de Postman y k6 | Responsable de QA |
| Una vez por entrega | Al menos 2 sesiones exploratorias (empezando por EX-5) | Responsable de QA |
| Al cierre del curso | CP-12 (aceptación pedagógica) | Docente o usuario |

---

## 12. Gestión de riesgos

### 12.1 Riesgos del producto (guían la estrategia basada en riesgos)

| Riesgo | Prob. | Impacto | Mitigación con pruebas |
|---|---|---|---|
| Un estudiante pierde su progreso o queda bloqueado | Media | Alto | Tablas de decisión de acceso y desbloqueo; upsert sin retrocesos; migraciones con datos antiguos |
| No puede recuperar el acceso (correo o código) | Media | Alto | Tabla de decisión de envío, límites de vencimiento e intentos, CP-07 con correo real |
| Acceso no autorizado o robo de cuenta | Baja | Alto | `test_seguridad.py`, códigos con hash, bloqueo a los 5 intentos y respuesta neutra |
| Redirecciones rotas detrás del proxy | Media | Alto | `test_proxy_redirecciones.py` y CP-02 |
| Errores con varios usuarios a la vez | Media | Medio | k6, prueba de concurrencia de migraciones y caché del contenido |
| Retos que aceptan respuestas incorrectas o rechazan correctas | Media | Medio | Partición de equivalencia del código y bloques que generan la solución |
| Contenido con ejemplos que no imprimen lo que dicen | Baja | Medio | Prueba que ejecuta los 16 ejemplos y retos de la teoría |

### 12.2 Riesgos del proyecto

| Riesgo | Mitigación |
|---|---|
| Credenciales SMTP expuestas en el repositorio (ya ocurrió) | Secretos de Codespaces; `.env` en `.gitignore`; revisar `git status` antes de cada commit |
| Falta de tiempo antes de una entrega | El smoke y la priorización por riesgo indican qué probar primero |
| Herramientas no disponibles (k6, Newman) | Están documentadas; mientras tanto se usa la medición preliminar en Python y la verificación de la colección |

---

## 13. Criterios de entrada, salida y suspensión

**Entrada** (para empezar a probar una versión):

- La aplicación arranca (`/health` responde 200).
- Las dependencias se instalan con `requirements.txt`.
- El smoke está en verde.

**Salida** (para dar una versión por lista):

- El 100 % de las pruebas automáticas aprobadas en la integración continua.
- Ningún defecto abierto de prioridad alta.
- Casos manuales CP-01 a CP-11 ejecutados y aprobados (o con desviaciones aceptadas y registradas).
- k6 cumple sus umbrales (p95 < 500 ms y menos de 1 % de errores).
- Cobertura de líneas de la aplicación de al menos 90 %.
- Cada defecto corregido en la versión tiene su prueba de regresión.

**Suspensión:** si el smoke falla, se detiene el resto de las pruebas hasta corregirlo.

| Criterio de salida (versión actual) | Estado |
|---|---|
| Pruebas automáticas | ✅ 217/217 |
| Defectos de prioridad alta abiertos | ✅ 0 |
| Cobertura de la aplicación ≥ 90 % | ✅ 94,1 % |
| Regresión de cada defecto | ✅ (sección 14) |
| Casos manuales CP-01 a CP-11 | ⏳ Pendiente del equipo (CP-01, CP-03, CP-05, CP-06 y CP-08 se verificaron durante el desarrollo con Playwright) |
| k6 | ⏳ Pendiente (medición preliminar: p95 = 43 ms, 0 errores) |

---

## 14. Registro de defectos y estrategia basada en defectos anteriores

| ID | Defecto | Cómo se encontró | Causa raíz | Corrección | Prueba de regresión |
|---|---|---|---|---|---|
| E01 | Tras iniciar sesión, evaluar un quiz o salir, el navegador iba a `localhost` (`ERR_CONNECTION_REFUSED`) | QA manual | Redirecciones absolutas construidas con el Host interno del proxy | `cc1361d` | `system/test_proxy_redirecciones.py` |
| E02 | Las respuestas del quiz se perdían al ir al reto y volver | QA manual | El resultado se guardaba en la sesión y se borraba al mostrarse | `9d6ebfa` | `system/test_aprendizaje.py::test_answers_survive_*` |
| E03/E04 | No llegaban los correos de cambio y recuperación, y el mensaje decía que sí | QA manual | Faltaba la configuración SMTP y se mostraba un éxito sin confirmación | `c93775f`, `adbcb56` | `system/test_contrasenas.py` |
| D-05 | No se podían repasar las lecciones de la unidad 2 | QA manual | Plantilla propia y duplicada sin el botón «Repasar» | `0e3f479` | `test_unit_two_lessons_can_be_reviewed_once_completed` |
| D-06 | Reto final exclusivo de la unidad 2, incoherente con el resto del curso | Revisión de diseño | Duplicaba la lección 4 y bloqueaba la unidad 3 | `0e3f479` | `test_unit_two_uses_the_common_unit_page_without_an_extra_final_challenge` |
| D-07 | Una unidad podía abrirse con la unidad anterior completada aunque las previas no lo estuvieran | **Tabla de decisión de este plan** | El desbloqueo miraba solo la unidad anterior, no toda la cadena | Entrega de QA | `test_unit_unlocking_decision_table` |
| D-08 | Con varios usuarios a la vez: errores 500 («duplicate column name») y esperas de hasta 5 s | **Medición de rendimiento de este plan** | La migración del esquema y el contenido se ejecutaban en cada conexión; dos primeras conexiones simultáneas chocaban, y leer el contenido estático en cada petición saturaba el proceso | Entrega de QA: inicialización una vez por proceso, `ALTER` tolerante y caché del contenido | `test_concurrent_first_connections_do_not_collide`, `test_adding_an_existing_column_is_tolerated`, `test_cached_course_content_is_copied_for_each_caller` |

Regla del equipo: **ningún defecto se da por corregido sin una prueba que falle antes del arreglo y pase después.** Así la tasa de defectos recurrentes se mantiene en cero y cada sesión exploratoria empieza por estas zonas (EX-5).

---

## 15. Matriz de trazabilidad

| Requisito | Pruebas automáticas | Casos manuales |
|---|---|---|
| RF-01 Registro | `unit/test_reglas_autenticacion.py` (nombre, correo, contraseña, duplicados); `system/test_autenticacion.py::test_registration_*` | CP-01 |
| RF-02 Sesión | `system/test_autenticacion.py::test_login_*`, `test_logout_clears_the_user_session`; `system/test_seguridad.py::test_session_cookie_*` | EX-4 |
| RF-03 Nivel | `unit/...::test_level_recommendation_decision_table`; `system/test_autenticacion.py::test_level_page_*` | – |
| RF-04 Desbloqueo | `system/test_aprendizaje.py::test_unit_unlocking_decision_table`, `test_lesson_access_decision_table`, `test_unit_two_*` | – |
| RF-05 Teoría | `integration/test_contenido.py` (los 16 ejemplos se ejecutan); `system/test_aprendizaje.py::test_lesson_page_shows_the_extended_theory` | CP-03, CP-12 |
| RF-06 Quiz | `system/test_aprendizaje.py::test_quiz_completion_boundary`, `test_answers_survive_*`, `test_repeat_*` | CP-03 |
| RF-07 Repaso | `test_reviewing_a_completed_lesson_never_resets_progress`, `test_unit_two_lessons_can_be_reviewed_once_completed`; `integration/...::test_progress_upsert_*` | CP-04 |
| RF-08 Retos | `unit/test_evaluacion_practica.py`; `system/test_practica.py` | CP-05, CP-06 |
| RF-09 Progreso | `test_completed_lesson_appears_in_progress`, `test_old_unit_two_puzzle_progress_is_kept_but_ignored`; smoke | – |
| RF-10 Contraseñas | `system/test_contrasenas.py` (16 funciones); `integration/test_repositorios.py::test_reset_code_*` | CP-07 |
| RF-11 Certificado | `system/test_certificado.py`; `integration/...::test_certificate_is_issued_once_per_student` | CP-08 |
| RF-12 API | `system/test_api.py` | Colección de Postman |
| RNF-01 Seguridad | `system/test_seguridad.py` (marcador `security`), además del bloqueo de códigos y la anti-enumeración en `test_contrasenas.py` | EX-2 |
| RNF-02 Proxy | `system/test_proxy_redirecciones.py` | CP-02 |
| RNF-03 Rendimiento | `qa/k6/carga_basica.js`; `integration/...::test_cached_course_content_is_copied_for_each_caller` | – |
| RNF-04 Confiabilidad | `integration/test_repositorios.py::test_schema_migration_*`, `test_concurrent_first_connections_*` | – |
| RNF-05 Usabilidad | – | CP-09, CP-10, CP-11 |

---

## 16. Métricas

| Métrica | Cómo se obtiene | Valor actual |
|---|---|---|
| % de pruebas ejecutadas | Casos ejecutados / casos planificados (automáticos y manuales) | Automáticos: 217/217 (100 %); manuales: pendientes del equipo |
| % de pruebas aprobadas / fallidas | Resumen de pytest y de la integración continua | 100 % / 0 % |
| Cobertura de líneas de la aplicación | `python -m pytest --cov=.` (sin contar `tests/`) | 94,1 % (1.147 líneas, 68 sin ejecutar) |
| Errores encontrados | Filas del registro de defectos (sección 14) | 8 en total: 6 por QA manual o revisión y 2 por este plan (D-07 y D-08) |
| Tiempo promedio de corrección | Fecha del commit de la corrección menos la fecha del reporte | E01–E04, D-05 y D-06: corregidos el mismo día del reporte; D-07 y D-08: el mismo día en que los detectaron las pruebas |
| Tasa de errores recurrentes | Defectos reabiertos / defectos corregidos | 0 % (cada uno tiene su prueba de regresión) |
| Rendimiento (p95, errores) | k6 (preliminar: generador en Python) | p95 = 43 ms y 0 % de errores con 20 usuarios |

**Observación:** `models/usuario_model.py` (fachada de compatibilidad citada en el README como ejemplo del patrón Facade) no lo importa ninguna parte de la aplicación, por eso no aparece en la cobertura. Se mantiene por su valor documental; si deja de necesitarse, puede eliminarse.

---

## 17. Entregables

| Entregable | Ubicación |
|---|---|
| Plan maestro de pruebas | `docs/plan_de_pruebas.md` (este documento) |
| Pruebas automáticas por nivel | `tests/unit/`, `tests/integration/`, `tests/system/`, `tests/smoke/` |
| Configuración y marcadores | `pytest.ini`, `tests/conftest.py`, `tests/helpers.py` |
| Integración continua | `.github/workflows/ci.yml` |
| Colección de la API | `qa/postman/Nivora_API.postman_collection.json` |
| Prueba de carga | `qa/k6/carga_basica.js` |
| Registro de defectos y métricas | Secciones 14 y 16 de este documento (actualizar en cada entrega) |
