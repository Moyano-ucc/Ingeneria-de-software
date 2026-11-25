// Prueba de carga básica de Nivora con k6 (plan de pruebas, sección rendimiento).
//
// Simula estudiantes que entran a la portada, consultan las lecciones y evalúan
// un quiz por la API. Solo usa rutas públicas, así que no crea cuentas ni
// modifica la base de datos.
//
// Ejecución (con Nivora corriendo):
//   k6 run qa/k6/carga_basica.js
//   k6 run -e BASE_URL=https://<tu-codespace>-8000.app.github.dev qa/k6/carga_basica.js
//
// Criterio de aceptación (umbrales): menos de 1 % de errores y el 95 % de las
// respuestas en menos de 500 ms con 20 usuarios simultáneos.
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';

export const options = {
    stages: [
        { duration: '30s', target: 10 }, // subida gradual
        { duration: '1m', target: 20 },  // carga sostenida: un grupo de clase
        { duration: '30s', target: 0 },  // bajada
    ],
    thresholds: {
        http_req_failed: ['rate<0.01'],
        http_req_duration: ['p(95)<500'],
    },
};

export default function () {
    const home = http.get(`${BASE_URL}/`);
    check(home, { 'portada 200': (r) => r.status === 200 });

    const lessons = http.get(`${BASE_URL}/api/lecciones`);
    check(lessons, {
        'lecciones 200': (r) => r.status === 200,
        '16 lecciones': (r) => r.json('lecciones').length === 16,
    });

    const evaluation = http.post(
        `${BASE_URL}/api/lecciones/variables/evaluar`,
        JSON.stringify({ answers: ['nombre', 'int', 'True'] }),
        { headers: { 'Content-Type': 'application/json' } },
    );
    check(evaluation, { 'evaluación completa': (r) => r.json('completada') === true });

    const login = http.get(`${BASE_URL}/login`);
    check(login, { 'login 200': (r) => r.status === 200 });

    sleep(1); // tiempo de lectura entre páginas
}
