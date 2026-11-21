(function () {
    const form = document.querySelector('[data-registration-form] form');
    if (!form) return;

    form.addEventListener('submit', function (event) {
        const errors = validate();
        form.querySelectorAll('input').forEach((input) => {
            setFieldError(input.name, errors[input.name] || '');
        });
        if (Object.keys(errors).length) {
            event.preventDefault();
            form.querySelector(`[name="${Object.keys(errors)[0]}"]`).focus();
        }
    });

    form.querySelectorAll('input').forEach((input) => {
        input.addEventListener('input', () => {
            const errors = validate();
            setFieldError(input.name, errors[input.name] || '');
            if (input.name === 'password') {
                setFieldError('confirmacion', errors.confirmacion || '');
            }
        });
    });

    function validate() {
        const errors = {};
        const name = form.elements.nombre.value.trim();
        const password = form.elements.password.value;
        const confirmation = form.elements.confirmacion.value;
        if (name.length < 2 || name.length > 30) {
            errors.nombre = 'El nombre debe tener entre 2 y 30 caracteres.';
        }
        if (!form.elements.email.validity.valid) {
            errors.email = 'Escribe un correo válido, por ejemplo: nombre@correo.com.';
        }
        if (password.length < 8 || !/\p{L}/u.test(password) || !/\d/.test(password)) {
            errors.password = 'Usa al menos 8 caracteres, con letras y números.';
        }
        if (confirmation !== password) {
            errors.confirmacion = 'Las contraseñas no coinciden.';
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