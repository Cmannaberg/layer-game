// Prize amounts indexed by clue number (0 = after first clue, 4 = after fifth clue)
const PRIZES = [10000, 7500, 5000, 2500, 1000];

let gameState = {
    questions: [],
    currentQuestionIndex: 0,
    currentClueIndex: 0,   // number of clues revealed so far
    totalScore: 0,
    roundResults: [],
    roundOver: false,
};

// ─── Utilities ───────────────────────────────────────────────────────────────

function shuffle(array) {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
}

function formatMoney(amount) {
    return amount.toLocaleString();
}

function currentPrize() {
    // Prize is determined by how many clues have been revealed.
    // After clue 1 (currentClueIndex === 1) → PRIZES[0]
    const idx = Math.min(Math.max(gameState.currentClueIndex - 1, 0), PRIZES.length - 1);
    return PRIZES[idx];
}

// ─── Screen management ───────────────────────────────────────────────────────

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
}

// ─── Game flow ───────────────────────────────────────────────────────────────

function startGame() {
    // Pick 5 random questions each game
    gameState.questions = shuffle(QUESTIONS).slice(0, 5);
    gameState.currentQuestionIndex = 0;
    gameState.totalScore = 0;
    gameState.roundResults = [];

    document.getElementById('total-questions').textContent = gameState.questions.length;
    showScreen('game-screen');
    loadQuestion();
}

function loadQuestion() {
    gameState.currentClueIndex = 0;
    gameState.roundOver = false;

    const question = gameState.questions[gameState.currentQuestionIndex];

    // Header
    document.getElementById('question-num').textContent = gameState.currentQuestionIndex + 1;
    document.getElementById('total-score').textContent = formatMoney(gameState.totalScore);
    document.getElementById('category').textContent = question.category;

    // Clear clues
    document.getElementById('clues-area').innerHTML = '';

    // Reset input
    const input = document.getElementById('guess-input');
    input.value = '';
    input.disabled = false;
    input.focus();

    // Reset buttons
    setButtonStates(false);
    hideFeedback();

    // Reveal the first clue automatically
    revealNextClue();
}

function revealNextClue() {
    if (gameState.roundOver) return;

    const question = gameState.questions[gameState.currentQuestionIndex];

    if (gameState.currentClueIndex >= question.clues.length) return;

    const clueText = question.clues[gameState.currentClueIndex];
    const clueNumber = gameState.currentClueIndex + 1;
    const prize = PRIZES[gameState.currentClueIndex] !== undefined
        ? PRIZES[gameState.currentClueIndex]
        : PRIZES[PRIZES.length - 1];

    // Build clue card using DOM methods (avoids innerHTML with dynamic content)
    const card = document.createElement('div');
    card.className = 'clue-card';

    const body = document.createElement('div');
    body.className = 'clue-body';

    const numEl = document.createElement('div');
    numEl.className = 'clue-number';
    numEl.textContent = 'Clue #' + clueNumber;

    const textEl = document.createElement('div');
    textEl.className = 'clue-text';
    textEl.textContent = clueText;

    const prizeEl = document.createElement('div');
    prizeEl.className = 'prize-tag';
    prizeEl.textContent = '$' + formatMoney(prize);

    body.appendChild(numEl);
    body.appendChild(textEl);
    card.appendChild(body);
    card.appendChild(prizeEl);

    document.getElementById('clues-area').appendChild(card);
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    gameState.currentClueIndex++;
    updatePrizeDisplay();
    hideFeedback();

    // Disable "Next Clue" when all clues are shown
    const allShown = gameState.currentClueIndex >= question.clues.length;
    document.getElementById('next-clue-btn').disabled = allShown;
}

function updatePrizeDisplay() {
    document.getElementById('current-prize').textContent = formatMoney(currentPrize());
}

function submitGuess() {
    if (gameState.roundOver) return;

    const input = document.getElementById('guess-input');
    const raw = input.value.trim();
    if (!raw) return;

    const guess = raw.toLowerCase();
    const question = gameState.questions[gameState.currentQuestionIndex];

    // The player's guess must exactly equal the accepted answer, or contain it
    // as a whole-word phrase (word boundaries prevent e.g. "honeymoon" matching "moon").
    const isCorrect = question.acceptedAnswers.some(accepted => {
        const a = accepted.toLowerCase();
        if (guess === a) return true;
        const escaped = a.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        return new RegExp('\\b' + escaped + '\\b').test(guess);
    });

    if (isCorrect) {
        const prize = currentPrize();
        const cluesUsed = gameState.currentClueIndex;
        showFeedback(
            '🎉 Correct! The answer is "' + question.answer + '"! You won $' + formatMoney(prize) + '!',
            'correct'
        );
        endRound(true, prize, cluesUsed);
    } else {
        showFeedback('❌ Not quite — try again or reveal another clue.', 'wrong');
        input.value = '';
        input.focus();
    }
}

function skipQuestion() {
    if (gameState.roundOver) return;
    const question = gameState.questions[gameState.currentQuestionIndex];
    showFeedback('The answer was: ' + question.answer, 'info');
    endRound(false, 0, gameState.currentClueIndex);
}

function endRound(won, prize, cluesUsed) {
    gameState.roundOver = true;
    const question = gameState.questions[gameState.currentQuestionIndex];

    gameState.roundResults.push({
        answer: question.answer,
        category: question.category,
        won: won,
        prize: prize,
        cluesUsed: cluesUsed
    });

    if (won) {
        gameState.totalScore += prize;
        document.getElementById('total-score').textContent = formatMoney(gameState.totalScore);
    }

    setButtonStates(true);
    document.getElementById('guess-input').disabled = true;

    // Auto-advance after a short delay
    setTimeout(() => {
        gameState.currentQuestionIndex++;
        if (gameState.currentQuestionIndex >= gameState.questions.length) {
            showResults();
        } else {
            loadQuestion();
        }
    }, 3000);
}

// Disable/enable action buttons
function setButtonStates(disabled) {
    document.getElementById('guess-btn').disabled = disabled;
    document.getElementById('next-clue-btn').disabled = disabled;
    document.getElementById('skip-btn').disabled = disabled;
}

// ─── Results ─────────────────────────────────────────────────────────────────

function showResults() {
    document.getElementById('final-score').textContent = formatMoney(gameState.totalScore);

    const container = document.getElementById('round-results');
    container.innerHTML = '';

    gameState.roundResults.forEach((r, i) => {
        const item = document.createElement('div');
        item.className = 'round-result-item';

        const num = document.createElement('span');
        num.className = 'result-num';
        num.textContent = '#' + (i + 1);

        const answer = document.createElement('span');
        answer.className = 'result-answer';
        answer.textContent = r.answer;

        const cat = document.createElement('span');
        cat.className = 'result-category';
        cat.textContent = r.category;

        const outcome = document.createElement('span');
        if (r.won) {
            outcome.className = 'round-won';
            const em = document.createElement('em');
            em.textContent = '(' + r.cluesUsed + ' clue' + (r.cluesUsed !== 1 ? 's' : '') + ')';
            outcome.textContent = '+$' + formatMoney(r.prize) + ' ';
            outcome.appendChild(em);
        } else {
            outcome.className = 'round-lost';
            outcome.textContent = 'No points';
        }

        item.appendChild(num);
        item.appendChild(answer);
        item.appendChild(cat);
        item.appendChild(outcome);
        container.appendChild(item);
    });

    showScreen('results-screen');
}

// ─── Feedback ────────────────────────────────────────────────────────────────

function showFeedback(message, type) {
    const el = document.getElementById('feedback');
    el.textContent = message;
    el.className = 'feedback ' + type;
}

function hideFeedback() {
    document.getElementById('feedback').className = 'feedback hidden';
}

// ─── Event listeners ─────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('start-btn').addEventListener('click', startGame);
    document.getElementById('guess-btn').addEventListener('click', submitGuess);
    document.getElementById('next-clue-btn').addEventListener('click', revealNextClue);
    document.getElementById('skip-btn').addEventListener('click', skipQuestion);
    document.getElementById('play-again-btn').addEventListener('click', startGame);

    document.getElementById('guess-input').addEventListener('keydown', e => {
        if (e.key === 'Enter') submitGuess();
    });
});
