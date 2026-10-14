(function () {
    const form = document.querySelector('[data-registration-form] form');
    if (!form) return;

    form.addEventListener('submit', function (event) {
        const name = form.elements.nombre.value.trim();
        const email = form.elements.email.value.trim();
        const password = form.elements.password.value;

        if (name.length < 2 || name.length > 30) {
            event.preventDefault();
            showNotice('El nombre debe tener entre 2 y 30 caracteres.');
        } else if (!form.elements.email.validity.valid) {
            event.preventDefault();
            showNotice('Escribe un correo válido, por ejemplo: nombre@correo.com.');
        } else if (password.length < 8) {
            event.preventDefault();
            showNotice('La contraseña debe tener al menos 8 caracteres.');
        }
    });

    function showNotice(message) {
        let notice = document.querySelector('.floating-notice');
        if (!notice) {
            notice = document.createElement('div');
            notice.className = 'floating-notice';
            document.body.appendChild(notice);
        }
        notice.textContent = message;
        notice.classList.add('is-visible');
        window.setTimeout(() => notice.classList.remove('is-visible'), 3500);
    }
})();