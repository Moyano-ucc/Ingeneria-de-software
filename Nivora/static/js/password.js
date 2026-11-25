// Live feedback for new passwords (registration and password reset).
// The rules mirror AuthService.password_is_strong; the server always
// validates again, this script only helps the user while typing.
(() => {
    const RULES = {
        length: (value) => value.length >= 8,
        letter: (value) => /\p{L}/u.test(value),
        digit: (value) => /\d/.test(value),
    };
    const PASSWORD_MESSAGE = 'Usa al menos 8 caracteres, con letras y números.';
    const MISMATCH_MESSAGE = 'Las contraseñas no coinciden.';

    document.querySelectorAll('[data-password-form]').forEach((form) => {
        const password = form.querySelector('input[name="password"]');
        const confirmation = form.querySelector('input[name="confirmacion"]');
        const rules = form.querySelector('[data-password-rules]');
        if (!password || !rules) return;

        const items = [...rules.querySelectorAll('[data-rule]')];
        const setError = (input, message) => {
            const error = document.getElementById(`${input.name}-error`);
            if (!error) return;
            error.textContent = message;
            error.hidden = !message;
            input.setAttribute('aria-invalid', String(Boolean(message)));
        };
        const isStrong = () => items.every((item) => RULES[item.dataset.rule](password.value));
        const matches = () => !confirmation || confirmation.value === password.value;

        const update = () => {
            items.forEach((item) => {
                const met = RULES[item.dataset.rule](password.value);
                item.classList.toggle('is-met', met);
                item.setAttribute('aria-label', `${item.textContent}: ${met ? 'cumplido' : 'pendiente'}`);
            });
            if (isStrong()) setError(password, '');
            if (confirmation && confirmation.value) {
                setError(confirmation, matches() ? '' : MISMATCH_MESSAGE);
                confirmation.classList.toggle('is-match', matches() && isStrong());
            }
        };

        password.addEventListener('input', update);
        if (confirmation) confirmation.addEventListener('input', update);
        update();

        form.addEventListener('submit', (event) => {
            const problems = [];
            if (!isStrong()) {
                setError(password, PASSWORD_MESSAGE);
                problems.push(password);
            }
            if (!matches()) {
                setError(confirmation, MISMATCH_MESSAGE);
                problems.push(confirmation);
            }
            if (!problems.length) return;
            // Another validator (e.g. registration) may already have focused a field.
            if (!event.defaultPrevented) problems[0].focus();
            event.preventDefault();
        });
    });
})();
