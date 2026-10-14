(() => {
    const puzzle = document.querySelector('[data-code-puzzle]');
    if (!puzzle) return;

    const available = puzzle.querySelector('[data-puzzle-available]');
    const board = puzzle.querySelector('[data-puzzle-board]');
    const empty = puzzle.querySelector('[data-puzzle-empty]');
    const sequenceInput = puzzle.querySelector('[data-puzzle-sequence]');
    const live = puzzle.querySelector('[data-puzzle-live]');
    const pieces = new Map(
        [...available.querySelectorAll('[data-piece-id]')].map((piece) => [
            piece.dataset.pieceId,
            piece.dataset.code,
        ]),
    );
    let order = [];

    const render = () => {
        board.replaceChildren();
        order.forEach((id, index) => {
            const row = document.createElement('li');
            row.className = 'puzzle-board-row';
            const code = document.createElement('code');
            code.textContent = pieces.get(id);
            row.append(code);

            const controls = document.createElement('span');
            controls.className = 'puzzle-piece-controls';
            [
                { label: 'Subir bloque', symbol: '↑', offset: -1 },
                { label: 'Bajar bloque', symbol: '↓', offset: 1 },
                { label: 'Quitar bloque', symbol: '×', remove: true },
            ].forEach((control) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'puzzle-control';
                button.setAttribute('aria-label', control.label);
                button.textContent = control.symbol;
                button.disabled = control.remove ? false : index + control.offset < 0 || index + control.offset >= order.length;
                button.addEventListener('click', () => {
                    if (control.remove) {
                        order.splice(index, 1);
                    } else {
                        const target = index + control.offset;
                        [order[index], order[target]] = [order[target], order[index]];
                    }
                    render();
                });
                controls.append(button);
            });
            row.append(controls);
            board.append(row);
        });

        available.querySelectorAll('[data-piece-id]').forEach((button) => {
            button.disabled = order.includes(button.dataset.pieceId);
        });
        empty.hidden = order.length > 0;
        sequenceInput.value = JSON.stringify(order);
        live.textContent = `${order.length} bloques en el programa.`;
    };

    available.addEventListener('click', (event) => {
        const button = event.target.closest('[data-piece-id]');
        if (!button || button.disabled) return;
        order.push(button.dataset.pieceId);
        render();
    });

    puzzle.querySelector('[data-puzzle-clear]').addEventListener('click', () => {
        order = [];
        render();
    });

    try {
        const initialOrder = JSON.parse(puzzle.dataset.initialOrder || '[]');
        if (Array.isArray(initialOrder)) {
            order = initialOrder.filter((id) => pieces.has(id));
        }
    } catch {
        order = [];
    }
    render();
})();