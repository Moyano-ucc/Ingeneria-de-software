(function () {
    const form = document.querySelector('[data-registration-form] form');
    if (!form) return;

    // Name and e-mail are checked here; the password and its confirmation
    // are handled by password.js, shared with the password reset form.
    form.addEventListener('submit', function (event) {
        const errors = validate();
        ['nombre', 'email'].forEach((name) => setFieldError(name, errors[name] || ''));
        if (Object.keys(errors).length) {
            event.preventDefault();
            form.querySelector(`[name="${Object.keys(errors)[0]}"]`).focus();
        }
    });

    form.querySelectorAll('input').forEach((input) => {
        input.addEventListener('input', () => {
            const errors = validate();
            if (input.name === 'nombre' || input.name === 'email') {
                setFieldError(input.name, errors[input.name] || '');
            }
        });
    });

    function validate() {
        const errors = {};
        const name = form.elements.nombre.value.trim();
        if (name.length < 2 || name.length > 30) {
            errors.nombre = 'El nombre debe tener entre 2 y 30 caracteres.';
        }
        if (!form.elements.email.validity.valid) {
            errors.email = 'Escribe un correo válido, por ejemplo: nombre@correo.com.';
        }
        return errors;
    }

    function setFieldError(name, message) {
        const input = form.elements[name];
        const error = document.getElementById(`${name}-error`);
        if (!input || !error) return;
        error.textContent = message;
        error.hidden = !message;
        input.setAttribute('aria-invalid', String(Boolean(message)));
    }
})();