// Block mode for easy exercises: the student builds the code by tapping
// tokens instead of typing it. The generated code is written into the same
// textarea, so the server evaluates it exactly like typed code. Without
// JavaScript the textarea keeps working as a normal editor.
(() => {
    const section = document.querySelector('[data-practice-blocks]');
    const textarea = document.getElementById('codigo');
    if (!section || !textarea) return;

    const tokens = JSON.parse(section.dataset.fichas || '[]');
    const bank = section.querySelector('[data-blocks-bank]');
    const toggle = document.querySelector('[data-blocks-toggle]');
    const modeInput = document.querySelector('[data-blocks-mode-input]');
    const newline = section.querySelector('[data-blocks-newline]');
    const undo = section.querySelector('[data-blocks-undo]');
    const clear = section.querySelector('[data-blocks-clear]');

    // Each line is a list of chunks; previous code is kept as one chunk per line.
    const fromText = (text) => {
        const rows = text.split('\n').map((line) => line.trim()).filter(Boolean);
        return rows.length ? rows.map((line) => [line]) : [[]];
    };
    let lines = fromText(textarea.value);

    const render = () => {
        textarea.value = lines
            .map((line) => line.join(' '))
            .join('\n')
            .replace(/\n+$/, '');
        const current = lines[lines.length - 1];
        newline.disabled = current.length === 0;
        undo.disabled = lines.length === 1 && current.length === 0;
    };

    tokens.forEach((token) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'practice-token';
        button.textContent = token;
        button.setAttribute('aria-label', `Agregar ${token}`);
        button.addEventListener('click', () => {
            lines[lines.length - 1].push(token);
            render();
        });
        bank.append(button);
    });

    newline.addEventListener('click', () => {
        lines.push([]);
        render();
    });
    undo.addEventListener('click', () => {
        const current = lines[lines.length - 1];
        if (current.length) current.pop();
        else if (lines.length > 1) lines.pop();
        render();
    });
    clear.addEventListener('click', () => {
        lines = [[]];
        render();
    });

    const setMode = (mode) => {
        const blocks = mode === 'bloques';
        section.hidden = !blocks;
        textarea.readOnly = blocks;
        textarea.classList.toggle('is-generated', blocks);
        modeInput.value = mode;
        toggle.textContent = blocks ? 'Prefiero escribir el código' : 'Prefiero usar bloques';
        if (blocks) {
            lines = fromText(textarea.value);
            render();
        }
    };

    toggle.hidden = false;
    toggle.addEventListener('click', () => {
        setMode(section.hidden ? 'bloques' : 'escribir');
    });
    setMode(section.dataset.mode === 'escribir' ? 'escribir' : 'bloques');
})();
