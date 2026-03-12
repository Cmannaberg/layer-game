#!/usr/bin/env python3
"""Illuminate — The clue guessing game."""

import json
import random
import os
import sys
import select
import time
import difflib

try:
    import anthropic as _anthropic
    _AI_AVAILABLE = True
except ImportError:
    _AI_AVAILABLE = False

COSTS      = [1, 5, 10, 25, 50]   # clue prices: cheapest (vague) → priciest (specific)
GUESS_SEC  = 20
FUZZY_THRESHOLD = 0.75             # similarity ratio to accept a close spelling
Q_FILE     = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'questions.json')

class QuitGame(Exception):
    pass

# ── display helpers ───────────────────────────────────────────────────────────

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def hr(ch='─', w=58):
    print(ch * w)

def banner(title):
    hr('═')
    print(f'  {title}')
    hr('═')

def illuminate_moment(winner, prize):
    """Flash the Illuminate logo in ASCII when someone gets a correct answer."""
    clear()
    print()
    print('         ' + '·  ' * 12)
    print('              ✦       ✦       ✦')
    print('                  \\   |   /')
    print('              ✦ ───  💡  ─── ✦')
    print('                  /   |   \\')
    print('              ✦       ✦       ✦')
    print('         ' + '·  ' * 12)
    print()
    print('            /              \\')
    print('           /   ◉       ◉   \\')
    print('          |        ‿        |')
    print('           \\               /')
    print('            \\_____________/')
    print()
    print('  ' + '═' * 38)
    print(f'   ✨  I L L U M I N A T E D  ✨')
    print('  ' + '═' * 38)
    print(f'\n    {winner} wins {fmt_money(prize)}!\n')
    time.sleep(3)

def fmt_money(n):
    return f'${n:,}'

def show_scores(scores, prize_pot=None):
    hr()
    for name, bal in scores.items():
        print(f'  {name:<24}{fmt_money(bal):>10}')
    if prize_pot is not None:
        print(f'  {"Prize pot":<24}{fmt_money(prize_pot):>10}')
    hr()

def show_clues(revealed):
    if not revealed:
        return
    print('\n  Clues revealed so far:')
    for i, (cost, text) in enumerate(revealed, 1):
        print(f'    {i}. [{fmt_money(cost)}] {text}')

# ── timed input ───────────────────────────────────────────────────────────────

def timed_input(prompt, sec=GUESS_SEC):
    """Return stripped input, or None if time runs out (Unix/macOS only)."""
    print(prompt, end='', flush=True)
    start = time.time()
    while True:
        remaining = sec - (time.time() - start)
        if remaining <= 0:
            print('\n  ⏰ Time\'s up!')
            return None
        ready, _, _ = select.select([sys.stdin], [], [], min(0.2, remaining))
        if ready:
            val = sys.stdin.readline().strip()
            if val.lower() in ('quit', 'q'):
                raise QuitGame
            return val

# ── quit-aware input & fuzzy match ───────────────────────────────────────────

def ask(prompt):
    """input() that raises QuitGame if the user types 'quit' or 'q'."""
    val = input(prompt).strip()
    if val.lower() in ('quit', 'q'):
        raise QuitGame
    return val

def is_correct(guess, answer):
    """Return True if guess matches answer (case-insensitive, close spelling OK)."""
    g = guess.strip().lower()
    a = answer.strip().lower()
    if g == a:
        return True
    ratio = difflib.SequenceMatcher(None, g, a).ratio()
    return ratio >= FUZZY_THRESHOLD

# ── AI question generation ────────────────────────────────────────────────────

def _claude_client():
    """Return an Anthropic client, or None if unavailable."""
    if not _AI_AVAILABLE:
        return None
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return None
    return _anthropic.Anthropic(api_key=api_key)

def _question_from_claude(client, concept, description, category):
    """Ask Claude to generate a game question from a concept + description."""
    response = client.messages.create(
        model='claude-haiku-4-5',
        max_tokens=512,
        messages=[{
            'role': 'user',
            'content': f"""Create a trivia question for a guessing game about this concept:

Name: {concept}
Description: {description}
Category: {category}

Return ONLY valid JSON, no extra text:
{{
  "answer": "{concept}",
  "category": "{category}",
  "clues": [
    "Very vague clue — could apply to many things ($1)",
    "Narrows to a general domain ($5)",
    "Points clearly to this topic area ($10)",
    "Very close to the answer ($25)",
    "Almost gives it away using different wording ($50)"
  ]
}}

Rules: clues go from vague to specific. Never use the answer word in any clue."""
        }]
    )
    text = response.content[0].text.strip()
    if text.startswith('```'):
        text = text.split('```')[1]
        if text.startswith('json'):
            text = text[4:]
    return json.loads(text.strip())

def _save_question(q):
    """Append a question to questions.json."""
    existing = json.load(open(Q_FILE))
    existing.append(q)
    with open(Q_FILE, 'w') as f:
        json.dump(existing, f, indent=2)

def fetch_sefaria_question(subcategory='random'):
    """
    Fetch a random topic from Sefaria.org and use Claude to generate a question.
    subcategory: 'people' | 'concepts' | 'random'
    """
    import urllib.request

    client = _claude_client()
    if not client:
        print('  ✗ ANTHROPIC_API_KEY not set — needed to generate clues from Sefaria text.')
        return None

    print('  Fetching topic from Sefaria…', end='', flush=True)
    try:
        # Sample across multiple offsets for variety
        offset = random.choice([0, 200, 400])
        url = f'https://www.sefaria.org/api/topics?limit=200&offset={offset}'
        with urllib.request.urlopen(url, timeout=8) as resp:
            topics = json.loads(resp.read())

        # Filter to topics with English descriptions
        rich = [t for t in topics if t.get('description', {}).get('en', '').strip()]

        if subcategory == 'people':
            # Heuristic: titles/names typically have "Rabbi", a proper name, or known figures
            people_keywords = ['rabbi', 'king', 'prophet', 'born', 'lived', 'led', 'son of',
                               'disciple', 'scholar', 'patriarch', 'matriarch', 'priest']
            pool = [t for t in rich if any(
                kw in t.get('description', {}).get('en', '').lower()
                for kw in people_keywords
            )]
            category = 'Sefaria — People & Sages'
        elif subcategory == 'concepts':
            # Heuristic: concepts don't sound like people names
            people_keywords = ['rabbi', 'born', 'lived', 'son of', 'disciple']
            pool = [t for t in rich if not any(
                kw in t.get('description', {}).get('en', '').lower()
                for kw in people_keywords
            )]
            category = 'Sefaria — Concepts & Practices'
        else:
            pool = rich
            category = 'Sefaria — Jewish Library'

        if not pool:
            pool = rich  # fallback

        topic = random.choice(pool)
        name  = topic.get('en', topic.get('primaryTitle', {}).get('en', 'Unknown'))
        desc  = topic['description']['en']

        print(f' got "{name}". Generating clues…', end='', flush=True)
        q = _question_from_claude(client, name, desc, category)
        _save_question(q)
        print(' done (saved to questions.json).')
        return q

    except Exception as e:
        print(f'\n  ✗ Sefaria fetch failed: {e}')
        return None

def generate_question(topic):
    """Call Claude to generate a question with 5 clues for a free-form topic."""
    client = _claude_client()
    if not client:
        print('  ✗ ANTHROPIC_API_KEY not set.')
        return None

    print(f'  Generating question about "{topic}"…', end='', flush=True)
    try:
        response = client.messages.create(
            model='claude-haiku-4-5',
            max_tokens=512,
            messages=[{
                'role': 'user',
                'content': f"""Create a trivia question for a guessing game about: {topic}

Return ONLY valid JSON, no extra text:
{{
  "answer": "The specific answer (a person, place, event, or thing)",
  "category": "{topic}",
  "clues": [
    "Very vague clue — could describe many things ($1)",
    "Narrows to a general domain ($5)",
    "Points to the specific topic area ($10)",
    "Very close to the answer ($25)",
    "Almost gives it away using different wording ($50)"
  ]
}}

Rules: clues must go from vague to specific. Never use the answer word in a clue."""
            }]
        )
        text = response.content[0].text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        q = json.loads(text.strip())
        _save_question(q)
        print(' done (saved to questions.json).')
        return q
    except Exception as e:
        print(f'\n  ✗ Generation failed: {e}')
        return None

# ── category selection ────────────────────────────────────────────────────────

def category_select(all_questions):
    """
    Show a category picker. Returns the filtered+augmented question list.
    """
    clear()
    banner('SELECT CATEGORIES')

    ai_ready = _AI_AVAILABLE and bool(os.environ.get('ANTHROPIC_API_KEY'))

    # Build category list from the database
    cats = sorted(set(q.get('category', 'General') for q in all_questions))
    selected = set()              # nothing selected by default — Sefaria is the default source
    ai_topics = []                # user-added free-form AI topics
    sefaria_requests = []         # ('random'|'people'|'concepts', count)

    while True:
        clear()
        banner('SELECT QUESTION SOURCES')

        # ── Sefaria / AI section (shown first) ──
        print('  SEFARIA & AI  (generated questions)\n')
        if ai_ready:
            print('  [s]  Sefaria Jewish Library')
            print('  [a]  AI topic of your choice')
        else:
            print('  (Set ANTHROPIC_API_KEY to enable Sefaria & AI generation)')

        if sefaria_requests:
            summary = ', '.join(f'{n}× {t}' for t, n in sefaria_requests)
            print(f'\n  Sefaria queued : {summary}')
        if ai_topics:
            print(f'  AI queued      : {", ".join(ai_topics)}')

        # ── Pre-written section ──
        print('\n  PRE-WRITTEN QUESTIONS  (toggle with number)\n')
        for i, cat in enumerate(cats, 1):
            mark = '✓' if cat in selected else ' '
            print(f'  [{mark}] {i:>2}.  {cat}')

        print('\n  (s) Sefaria  |  (a) AI topic  |  number to toggle  |  Enter to start')
        choice = ask('\n  → ').strip().lower()

        if choice == '':
            break
        elif choice == 's':
            if not ai_ready:
                print('  Set ANTHROPIC_API_KEY first.')
                input('  Press Enter…')
            else:
                print('\n  Sefaria sub-category:')
                print('    1. People & Sages (rabbis, biblical figures)')
                print('    2. Concepts & Practices (holidays, laws, ideas)')
                print('    3. Random (anything in the library)')
                sub = ask('  Choose (1/2/3): ').strip()
                submap = {'1': 'people', '2': 'concepts', '3': 'random'}
                subcat = submap.get(sub, 'random')
                try:
                    n = int(ask('  How many questions? ').strip())
                    n = max(1, min(n, 10))
                except ValueError:
                    n = 1
                sefaria_requests.append((subcat, n))
        elif choice == 'a':
            if not ai_ready:
                print('  Set ANTHROPIC_API_KEY first.')
                input('  Press Enter…')
            else:
                topic = ask('  Topic (e.g. "Jazz musicians"): ').strip()
                if topic:
                    ai_topics.append(topic)
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(cats):
                cat = cats[idx]
                if cat in selected:
                    selected.discard(cat)
                else:
                    selected.add(cat)

    # Filter pre-written questions to selected categories
    pool = [q for q in all_questions if q.get('category', 'General') in selected]

    # Generate free-form AI questions
    for topic in ai_topics:
        q = generate_question(topic)
        if q:
            pool.append(q)

    # Generate Sefaria questions
    for subcat, n in sefaria_requests:
        for _ in range(n):
            q = fetch_sefaria_question(subcat)
            if q:
                pool.append(q)

    if not pool:
        print('\n  No questions in pool — using all pre-written questions as fallback.')
        input('  Press Enter…')
        return list(all_questions)

    random.shuffle(pool)
    return pool

# ── game setup ────────────────────────────────────────────────────────────────

def setup():
    clear()
    banner('✨  I L L U M I N A T E  ✨')
    print('  Guess the answer using as few clues as possible.\n')

    def ask_int(prompt, lo=1, hi=None):
        while True:
            try:
                v = int(input(f'  {prompt}: '))
                if v >= lo and (hi is None or v <= hi):
                    return v
            except ValueError:
                pass
            bound = f' (minimum {lo})' if hi is None else f' ({lo}–{hi})'
            print(f'  Please enter a valid whole number{bound}.')

    n = ask_int('How many players', lo=1)
    players = []
    for i in range(n):
        name = input(f'  Player {i + 1} name: ').strip() or f'Player {i + 1}'
        players.append(name)

    pot    = ask_int('Starting pot per player ($)', lo=1)
    rounds = ask_int('Number of regular rounds (a Final Round follows automatically)', lo=1)

    print(f'\n  {n} player(s): {", ".join(players)}')
    print(f'  Starting pot: {fmt_money(pot)} each')
    print(f'  {rounds} regular round(s) + 1 Final Round')
    input('\n  Press Enter to start the game…')
    return players, pot, rounds

# ── guessing phase ────────────────────────────────────────────────────────────

def guess_phase(players, scores, answer, prize_pot, start_idx=0):
    """
    Give each player GUESS_SEC seconds to guess in turn (starting from start_idx).
    Return the winner's name, or None if no one guesses correctly.
    """
    n = len(players)
    for offset in range(n):
        guesser = players[(start_idx + offset) % n]
        print(f'\n  {guesser} — {GUESS_SEC}s to guess (press Enter to pass):')
        raw = timed_input('  > ')
        if raw is None or raw == '':
            print(f'  {guesser} passes.')
            continue
        if is_correct(raw, answer):
            scores[guesser] += prize_pot
            illuminate_moment(guesser, prize_pot)
            return guesser
        else:
            print(f'  ✗ "{raw}" — not correct.')
    return None

# ── regular round ─────────────────────────────────────────────────────────────

def play_round(q, players, scores, rnum, total, start_idx=0):
    clear()
    banner(f'ROUND {rnum} of {total}   ·   Category: {q.get("category", "General")}')
    show_scores(scores)

    clues     = q['clues']          # ordered general → specific
    costs     = COSTS[:len(clues)]
    revealed  = []
    prize_pot = 0
    buyer_idx = start_idx
    winner    = None

    while len(revealed) < len(clues) and winner is None:
        buyer = players[buyer_idx % len(players)]
        cost  = costs[len(revealed)]

        # If buyer can't afford, skip them
        if scores[buyer] < cost:
            print(f'\n  {buyer} cannot afford the next clue ({fmt_money(cost)}) — skipping.')
            buyer_idx += 1
            # If nobody can afford the next clue, end the round
            if all(scores[p] < cost for p in players):
                print('  Nobody can afford the next clue. Round over.')
                break
            continue

        # Show current state
        print(f'\n  {buyer}\'s turn — next clue costs {fmt_money(cost)}   |   balance: {fmt_money(scores[buyer])}')
        show_clues(revealed)

        choice = ask('\n  (b)uy clue  |  (g)uess now  |  (p)ass  |  (quit)  → ').lower()

        if choice == 'b':
            scores[buyer] -= cost
            prize_pot     += cost
            revealed.append((cost, clues[len(revealed)]))

            clear()
            banner(f'ROUND {rnum} of {total}   ·   Category: {q.get("category", "General")}')
            show_scores(scores, prize_pot)
            show_clues(revealed)
            print(f'\n  All players have {GUESS_SEC}s each to guess!')

            winner = guess_phase(players, scores, q['answer'], prize_pot,
                                 start_idx=buyer_idx % len(players))
            buyer_idx += 1

        elif choice == 'g':
            # Free guess attempt for the buyer only (no clue purchased)
            print(f'\n  {buyer} — {GUESS_SEC}s to guess:')
            raw = timed_input('  > ')
            if raw and is_correct(raw, q['answer']):
                scores[buyer] += prize_pot
                illuminate_moment(buyer, prize_pot)
                winner = buyer
            else:
                if raw:
                    print(f'  ✗ "{raw}" — not correct.')
                buyer_idx += 1

        else:  # pass
            buyer_idx += 1

    if winner is None:
        print(f'\n  Nobody guessed it. The answer was: {q["answer"]}')
    input('\n  Press Enter to continue…')
    return scores

# ── final round ───────────────────────────────────────────────────────────────

EXERCISES = [
    {'name': 'Jumping Jacks',   'value':  1},
    {'name': 'Push-ups',        'value':  5},
    {'name': 'Deep Squats',     'value': 10},
    {'name': 'Burpees',         'value': 20},
    {'name': 'Turkish Get-ups', 'value': 50},
]

def play_fitness_round(players, scores, rnum, total):
    clear()
    banner(f'ROUND {rnum} of {total}   ·   💪 Physical Fitness Challenge')
    show_scores(scores)

    print('\n  EXERCISE MENU  (each level can only be claimed once)\n')
    for i, ex in enumerate(EXERCISES, 1):
        print(f'    {i}.  {ex["name"]:<20}  ${ex["value"]} per rep')

    print('\n  Each player picks an exercise, states their reps, and does them.')
    print('  Other players watch and verify. Honor system — no penalty for falling short.')
    input('\n  Press Enter to begin…')

    available = list(range(len(EXERCISES)))   # indices of unclaimed exercises

    for player in players:
        clear()
        banner(f'ROUND {rnum} of {total}   ·   💪 Physical Fitness Challenge')
        show_scores(scores)

        if not available:
            print(f'\n  No exercises left — {player} sits this one out.')
            input('  Press Enter…')
            continue

        print(f'\n  {player}\'s turn!\n')
        print('  Available exercises:\n')
        for i in available:
            ex = EXERCISES[i]
            print(f'    {i+1}.  {ex["name"]:<20}  ${ex["value"]} per rep')

        # Choose exercise
        while True:
            try:
                choice = int(ask('\n  Choose exercise number: ').strip()) - 1
                if choice in available:
                    break
                print('  That exercise is already taken or invalid.')
            except ValueError:
                pass

        available.remove(choice)
        exercise = EXERCISES[choice]

        # State reps
        while True:
            try:
                reps = int(ask(f'  How many {exercise["name"]}? ').strip())
                if reps > 0:
                    break
            except ValueError:
                pass

        prize = reps * exercise['value']
        print(f'\n  {player} will attempt {reps} {exercise["name"]}')
        print(f'  Potential prize: ${prize}')
        print(f'\n  Other players — watch and verify!')
        input('\n  Press Enter to start the countdown…')

        for i in range(3, 0, -1):
            print(f'  {i}…', end='\r', flush=True)
            time.sleep(1)
        print('  GO! 💪          ')

        input(f'\n  Press Enter when finished…')

        completed = ask(f'\n  {player}, did you complete all {reps} {exercise["name"]}? (y/n): ').strip().lower()

        if completed == 'y':
            scores[player] += prize
            print(f'\n  ✓ Amazing! {player} wins ${prize}!')
        else:
            print(f'\n  Good effort! No prize this time — keep training!')

        input('\n  Press Enter for the next player…')

    clear()
    banner(f'ROUND {rnum} of {total}   ·   💪 Fitness Challenge — Results')
    show_scores(scores)
    input('\n  Press Enter to continue…')
    return scores

# ── final round ───────────────────────────────────────────────────────────────

def play_final(q, players, scores):
    clear()
    banner('FINAL ROUND')
    show_scores(scores)

    print('\n  One clue. One guess. Place your wager.\n')
    print(f'  Clue: {q["clues"][0]}\n')
    hr()

    wagers  = {}
    guesses = {}

    for p in players:
        bal = scores[p]
        print(f'\n  {p}   (balance: {fmt_money(bal)})')
        while True:
            try:
                w = int(ask(f'  Wager $1 – {fmt_money(bal)}: $'))
                if 1 <= w <= bal:
                    wagers[p] = w
                    break
            except ValueError:
                pass
            print('  Please enter a valid wager.')
        guesses[p] = ask('  Your guess: ')
        print()

    # Reveal results
    clear()
    banner('FINAL ROUND — RESULTS')
    print(f'\n  The answer was: {q["answer"]}\n')
    hr()

    for p in players:
        correct = is_correct(guesses[p], q['answer'])
        if correct:
            scores[p] += wagers[p]
            tag = f'✓ Correct! +{fmt_money(wagers[p])}'
        else:
            scores[p] -= wagers[p]
            tag = f'✗ Wrong!  -{fmt_money(wagers[p])}'
        print(f'  {p:<22} "{guesses[p]}"')
        print(f'  {"":<22} {tag}\n')

    input('  Press Enter to see final standings…')
    return scores

# ── game over ─────────────────────────────────────────────────────────────────

def game_over(scores):
    clear()
    banner('GAME OVER — FINAL STANDINGS')
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    medals = ['1st', '2nd', '3rd']
    print()
    for i, (name, bal) in enumerate(ranked):
        place = medals[i] if i < 3 else f'{i+1}th'
        print(f'  {place}  {name:<22}{fmt_money(bal):>10}')
    print(f'\n  🏆 Winner: {ranked[0][0]}')
    hr()

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    players, pot, num_rounds = setup()
    scores = {p: pot for p in players}

    all_questions = json.load(open(Q_FILE))
    questions = category_select(all_questions)

    # Separate fitness rounds from trivia — final round must be a trivia question
    fitness_qs = [q for q in questions if q.get('category') == 'Physical Fitness']
    trivia_qs  = [q for q in questions if q.get('category') != 'Physical Fitness']

    if len(trivia_qs) < 1:
        print('  No trivia questions available for the final round.')
        game_over(scores)
        return

    # Build round list: mix fitness in, but reserve last trivia q for the final
    round_qs = questions[:num_rounds]  # may include fitness
    # Ensure the final question is always a trivia question
    final_q = trivia_qs[-1]
    # Remove final_q from round pool if it ended up there
    round_qs = [q for q in round_qs if q is not final_q][:num_rounds]

    if len(round_qs) < num_rounds:
        num_rounds = len(round_qs)

    for r in range(1, num_rounds + 1):
        q = round_qs[r - 1]
        if q.get('category') == 'Physical Fitness':
            scores = play_fitness_round(players, scores, r, num_rounds)
        else:
            start_idx = (r - 1) % len(players)
            scores = play_round(q, players, scores, r, num_rounds, start_idx)

    scores = play_final(final_q, players, scores)
    game_over(scores)

if __name__ == '__main__':
    try:
        main()
    except QuitGame:
        print('\n\n  Thanks for playing! Goodbye.\n')
        sys.exit(0)
    except KeyboardInterrupt:
        print('\n\n  Thanks for playing! Goodbye.\n')
        sys.exit(0)
