(function () {
    const form = document.querySelector('[data-level-form] form');
    const quiz = document.querySelector('.level-quiz');
    if (!form || !quiz) return;

    form.querySelectorAll('input[name="nivel_inicial"]').forEach((input) => {
        input.addEventListener('change', () => {
            const showQuiz = input.value === 'quiz' && input.checked;
            quiz.hidden = !showQuiz;
            quiz.querySelectorAll('input[type="radio"]').forEach((answer) => {
                answer.required = showQuiz;
            });
        });
    });
})();