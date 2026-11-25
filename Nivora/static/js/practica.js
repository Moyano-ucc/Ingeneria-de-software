(() => {
    const puzzle = document.querySelector('[data-practice-puzzle]');
    if (!puzzle) return;

    const config = JSON.parse(puzzle.dataset.config);
    const initialAnswer = JSON.parse(puzzle.dataset.answer);
    const kind = puzzle.dataset.kind;
    const interaction = puzzle.querySelector('[data-practice-interaction]');
    const answerInput = puzzle.querySelector('[data-practice-answer]');
    const live = puzzle.querySelector('[data-practice-live]');
    const form = puzzle.closest('form');

    const addHeading = (parent, text) => {
        const heading = document.createElement('h3');
        heading.textContent = text;
        parent.append(heading);
    };

    const setAnswer = (answer) => {
        answerInput.value = JSON.stringify(answer);
    };

    const createButton = (text, className, handler) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = className;
        button.textContent = text;
        button.addEventListener('click', handler);
        return button;
    };

    if (kind === 'ordenar') {
        const blocks = new Map(config.bloques.map((block) => [block.id, block.texto]));
        const order = Array.isArray(initialAnswer)
            ? [...new Set(initialAnswer.filter((id) => blocks.has(id)))]
            : [];
        const bank = document.createElement('div');
        bank.className = 'practice-piece-bank';
        const board = document.createElement('ol');
        board.className = 'practice-order-board';
        const clear = createButton('Limpiar', 'btn-secondary', () => {
            order.length = 0;
            renderOrder();
        });

        addHeading(interaction, 'Bloques disponibles');
        interaction.append(bank);
        addHeading(interaction, 'Tu programa');
        interaction.append(board, clear);

        const shuffled = [...config.bloques];
        for (let index = shuffled.length - 1; index > 0; index -= 1) {
            const target = Math.floor(Math.random() * (index + 1));
            [shuffled[index], shuffled[target]] = [shuffled[target], shuffled[index]];
        }
        shuffled.forEach((block) => {
            bank.append(createButton(block.texto, 'practice-piece', () => {
                if (!order.includes(block.id)) order.push(block.id);
                renderOrder();
            }));
        });

        function renderOrder() {
            board.replaceChildren();
            order.forEach((id, index) => {
                const row = document.createElement('li');
                const code = document.createElement('code');
                code.textContent = blocks.get(id);
                row.append(code);

                const controls = document.createElement('span');
                controls.className = 'practice-piece-controls';
                [
                    { label: 'Subir bloque', symbol: '↑', offset: -1 },
                    { label: 'Bajar bloque', symbol: '↓', offset: 1 },
                    { label: 'Quitar bloque', symbol: '×', remove: true },
                ].forEach((control) => {
                    const button = createButton(
                        control.symbol,
                        'practice-piece-control',
                        () => {
                            if (control.remove) {
                                order.splice(index, 1);
                            } else {
                                const target = index + control.offset;
                                [order[index], order[target]] = [order[target], order[index]];
                            }
                            renderOrder();
                        },
                    );
                    button.setAttribute('aria-label', control.label);
                    button.disabled = control.remove
                        ? false
                        : index + control.offset < 0 || index + control.offset >= order.length;
                    controls.append(button);
                });
                row.append(controls);
                board.append(row);
            });
            bank.querySelectorAll('button').forEach((button, index) => {
                button.disabled = order.includes(shuffled[index].id);
            });
            live.textContent = `${order.length} ${order.length === 1 ? 'bloque colocado.' : 'bloques colocados.'}`;
            setAnswer(order);
        }

        form.addEventListener('submit', (event) => {
            if (order.length !== config.bloques.length) {
                event.preventDefault();
                live.textContent = 'Coloca todos los bloques antes de comprobar.';
            }
        });
        renderOrder();
        return;
    }

    if (kind === 'completar') {
        const options = new Map(
            config.huecos.flatMap((gap) =>
                gap.opciones.map((option) => [option.id, option.texto]),
            ),
        );
        const gapIds = new Set(config.huecos.map((gap) => gap.id));
        const selections = initialAnswer && typeof initialAnswer === 'object'
            ? Object.fromEntries(
                Object.entries(initialAnswer).filter(
                    ([gapId, optionId]) => gapIds.has(gapId) && options.has(optionId),
                ),
            )
            : {};
        let selectedOption = null;
        const tokenButtons = [];
        const code = document.createElement('pre');
        code.className = 'practice-code-preview';
        const bank = document.createElement('div');
        bank.className = 'practice-token-bank';
        addHeading(interaction, 'Completa el código');
        interaction.append(code);
        addHeading(interaction, 'Fichas');
        interaction.append(bank);

        const renderCode = () => {
            code.replaceChildren();
            config.partes.forEach((part, index) => {
                code.append(document.createTextNode(part));
                const gap = config.huecos[index];
                if (!gap) return;
                const selected = selections[gap.id];
                const button = createButton(
                    selected ? options.get(selected) : 'elige una ficha',
                    'practice-gap',
                    () => {
                        if (selectedOption) {
                            selections[gap.id] = selectedOption;
                            selectedOption = null;
                        } else {
                            delete selections[gap.id];
                        }
                        renderCode();
                    },
                );
                button.setAttribute('aria-label', `Espacio ${gap.id}`);
                if (selectedOption) button.classList.add('is-target');
                code.append(button);
            });
            tokenButtons.forEach(({ button, optionId }) => {
                button.classList.toggle('is-selected', selectedOption === optionId);
            });
            setAnswer(selections);
            const completedGaps = Object.keys(selections).length;
            live.textContent = selectedOption
                ? 'Ahora selecciona el espacio donde quieres colocar la ficha.'
                : `${completedGaps} ${completedGaps === 1 ? 'espacio completado.' : 'espacios completados.'}`;
        };

        config.huecos.flatMap((gap) => gap.opciones).forEach((option) => {
            const button = createButton(option.texto, 'practice-token', () => {
                selectedOption = selectedOption === option.id ? null : option.id;
                renderCode();
            });
            tokenButtons.push({ button, optionId: option.id });
            bank.append(button);
        });
        form.addEventListener('submit', (event) => {
            if (Object.keys(selections).length !== config.huecos.length) {
                event.preventDefault();
                live.textContent = 'Completa todos los espacios antes de comprobar.';
            }
        });
        renderCode();
        return;
    }

    if (kind === 'emparejar') {
        const leftItems = new Map(config.izquierda.map((item) => [item.id, item.texto]));
        const rightItems = new Map(config.derecha.map((item) => [item.id, item.texto]));
        const pairs = initialAnswer && typeof initialAnswer === 'object'
            ? Object.fromEntries(
                Object.entries(initialAnswer).filter(
                    ([leftId, rightId]) => leftItems.has(leftId) && rightItems.has(rightId),
                ),
            )
            : {};
        let selectedLeft = null;
        const columns = document.createElement('div');
        columns.className = 'practice-match-columns';
        const leftColumn = document.createElement('div');
        const rightColumn = document.createElement('div');
        addHeading(interaction, 'Une cada pieza con su función');
        addHeading(leftColumn, 'Pieza');
        addHeading(rightColumn, 'Significado');
        columns.append(leftColumn, rightColumn);
        interaction.append(columns);

        const renderPairs = () => {
            leftColumn.querySelectorAll('.practice-match-item').forEach((button) => button.remove());
            rightColumn.querySelectorAll('.practice-match-item').forEach((button) => button.remove());
            config.izquierda.forEach((item) => {
                const paired = pairs[item.id];
                const button = createButton(
                    paired ? `${item.texto} → ${rightItems.get(paired)}` : item.texto,
                    `practice-match-item${selectedLeft === item.id ? ' is-selected' : ''}`,
                    () => {
                        selectedLeft = selectedLeft === item.id ? null : item.id;
                        renderPairs();
                    },
                );
                button.setAttribute('aria-pressed', String(selectedLeft === item.id));
                leftColumn.append(button);
            });
            config.derecha.forEach((item) => {
                const owner = Object.keys(pairs).find((key) => pairs[key] === item.id);
                const button = createButton(
                    item.texto,
                    `practice-match-item${owner ? ' is-paired' : ''}`,
                    () => {
                        if (!selectedLeft) {
                            live.textContent = 'Primero elige una pieza de la columna izquierda.';
                            return;
                        }
                        Object.keys(pairs).forEach((key) => {
                            if (pairs[key] === item.id) delete pairs[key];
                        });
                        pairs[selectedLeft] = item.id;
                        selectedLeft = null;
                        renderPairs();
                    },
                );
                button.setAttribute('aria-pressed', String(Boolean(owner)));
                rightColumn.append(button);
            });
            setAnswer(pairs);
            const pairCount = Object.keys(pairs).length;
            live.textContent = `${pairCount} ${pairCount === 1 ? 'conexión realizada.' : 'conexiones realizadas.'}`;
        };

        form.addEventListener('submit', (event) => {
            if (Object.keys(pairs).length !== config.izquierda.length) {
                event.preventDefault();
                live.textContent = 'Conecta todas las piezas antes de comprobar.';
            }
        });
        renderPairs();
    }
})();
