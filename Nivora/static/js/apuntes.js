// «Mis apuntes»: the lesson page talks to the REST API with fetch, using
// GET (list), POST (create), PUT (edit the whole note), PATCH (star) and
// DELETE (remove). Text is always inserted with textContent (never as HTML).
(() => {
    const section = document.querySelector('[data-notes]');
    if (!section) return;

    const lesson = section.dataset.lesson;
    const form = section.querySelector('[data-notes-form]');
    const list = section.querySelector('[data-notes-list]');
    const statusLine = section.querySelector('[data-notes-status]');
    const API = '/api/apuntes';

    const say = (message) => { statusLine.textContent = message; };

    async function request(method, url, body) {
        const response = await fetch(url, {
            method,
            credentials: 'same-origin',
            headers: body ? { 'Content-Type': 'application/json' } : {},
            body: body ? JSON.stringify(body) : undefined,
        });
        if (response.status === 401) throw new Error('Tu sesión venció. Vuelve a iniciar sesión.');
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            const detail = Array.isArray(data.detail) ? data.detail[0].msg : data.detail;
            throw new Error(detail || 'No se pudo guardar. Inténtalo de nuevo.');
        }
        return response.status === 204 ? null : response.json();
    }

    function button(text, label, handler) {
        const element = document.createElement('button');
        element.type = 'button';
        element.className = 'note-action';
        element.textContent = text;
        element.setAttribute('aria-label', label);
        element.addEventListener('click', handler);
        return element;
    }

    function render(notes) {
        list.replaceChildren();
        if (!notes.length) {
            const empty = document.createElement('li');
            empty.className = 'notes-empty';
            empty.textContent = 'Todavía no tienes apuntes en esta lección.';
            list.append(empty);
            return;
        }
        notes.forEach((note) => {
            const item = document.createElement('li');
            item.className = `note${note.destacado ? ' is-starred' : ''}`;
            const text = document.createElement('p');
            text.textContent = note.contenido;
            const actions = document.createElement('div');
            actions.className = 'note-actions';
            actions.append(
                // PATCH: only the "destacado" field changes.
                button(note.destacado ? '★' : '☆', note.destacado ? 'Quitar destacado' : 'Destacar', async () => {
                    try {
                        await request('PATCH', `${API}/${note.id}`, { destacado: !note.destacado });
                        await load();
                    } catch (error) { say(error.message); }
                }),
                // PUT: the whole note is replaced with the edited version.
                button('Editar', 'Editar apunte', async () => {
                    const edited = window.prompt('Edita tu apunte:', note.contenido);
                    if (edited === null) return;
                    try {
                        await request('PUT', `${API}/${note.id}`, {
                            leccion: note.leccion, contenido: edited, destacado: note.destacado,
                        });
                        say('Apunte actualizado.');
                        await load();
                    } catch (error) { say(error.message); }
                }),
                // DELETE
                button('Eliminar', 'Eliminar apunte', async () => {
                    if (!window.confirm('¿Eliminar este apunte?')) return;
                    try {
                        await request('DELETE', `${API}/${note.id}`);
                        say('Apunte eliminado.');
                        await load();
                    } catch (error) { say(error.message); }
                }),
            );
            item.append(text, actions);
            list.append(item);
        });
    }

    // GET with a query parameter: only this lesson's notes.
    async function load() {
        try {
            render(await request('GET', `${API}?leccion=${encodeURIComponent(lesson)}`));
        } catch (error) { say(error.message); }
    }

    // POST
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const textarea = form.elements.contenido;
        try {
            await request('POST', API, { leccion: lesson, contenido: textarea.value });
            textarea.value = '';
            say('Apunte guardado.');
            await load();
        } catch (error) { say(error.message); }
    });

    load();
})();
