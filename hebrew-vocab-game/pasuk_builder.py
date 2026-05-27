#!/usr/bin/env python3
"""
pasuk_builder.py
Fetches famous pasukim (Bible verses) from the Sefaria API and builds
pasuk_questions.json — one entry per verse/word combo.

Each entry has:
  ref, book, hebrew_text, english_text, words[],
  quiz_word_idx, quiz_word, answer, wrong_choices[]

Run:
  python3 pasuk_builder.py            # build all
  python3 pasuk_builder.py --refresh  # rebuild from scratch
"""

import argparse, json, re, sys, time, random
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ── Files ────────────────────────────────────────────────────────────────────
VOCAB_FILE = Path(__file__).parent / "hebrew_vocab.json"
OUT_FILE   = Path(__file__).parent / "pasuk_questions.json"
SEFARIA    = "https://www.sefaria.org/api/texts/{}"
UA         = {"User-Agent": "hebrew-vocab-game/1.0"}

# ── Curated famous pasukim ───────────────────────────────────────────────────
# (sefaria_ref, book_key, quiz_bare_consonants, answer)
#
# sefaria_ref  — Book.Chapter.Verse (dot notation)
# book_key     — must match a key in hebrew_vocab.json for wrong choices
# quiz_bare    — Hebrew consonants only (no nikkud) of the word to highlight
#                Use the form that actually appears in the verse text
# answer       — English meaning to display as the correct answer
#
PASUKIM = [
    # ── Torah ─────────────────────────────────────────────────────────────
    ("Genesis.1.1",       "Genesis",       "אלהים",  "God"),
    ("Genesis.1.1",       "Genesis",       "הארץ",   "the earth"),
    ("Genesis.1.1",       "Genesis",       "השמים",  "the heavens"),
    ("Genesis.1.27",      "Genesis",       "האדם",   "humankind"),
    ("Genesis.28.16",     "Genesis",       "במקום",  "in this place"),
    ("Exodus.3.14",       "Exodus",        "אהיה",   "I am / I will be"),
    ("Exodus.20.8",       "Exodus",        "יום",    "day"),
    ("Leviticus.19.18",   "Leviticus",     "לרעך",   "your neighbor"),
    ("Numbers.6.24",      "Numbers",       "יברכך",  "may He bless you"),
    ("Deuteronomy.6.4",   "Deuteronomy",   "אחד",    "one"),
    ("Deuteronomy.6.5",   "Deuteronomy",   "לבבך",   "your heart"),
    ("Deuteronomy.30.19", "Deuteronomy",   "החיים",  "the life, the living"),
    # ── Nevi'im ───────────────────────────────────────────────────────────
    ("Joshua.1.9",        "Joshua",        "חזק",    "be strong"),
    ("Isaiah.6.3",        "Isaiah",        "קדוש",   "holy"),
    ("Isaiah.40.31",      "Isaiah",        "כח",     "strength, power"),
    ("Micah.6.8",         "Micah",         "משפט",   "justice, judgment"),
    # ── Ketuvim ───────────────────────────────────────────────────────────
    ("Psalms.23.1",       "Psalms",        "רעי",    "my shepherd"),
    ("Psalms.27.1",       "Psalms",        "אורי",   "my light"),
    ("Psalms.121.2",      "Psalms",        "עזרי",   "my help"),
    ("Proverbs.3.5",      "Proverbs",      "בטח",    "trust"),
    ("Ruth.1.16",         "Ruth",          "תלכי",   "you go"),
    ("Ecclesiastes.3.1",  "Ecclesiastes",  "זמן",    "appointed time, season"),
]

# ── Hebrew text utilities ─────────────────────────────────────────────────────

def strip_cantillation(s):
    """Remove cantillation (trop) marks; keep nikkud (vowels)."""
    # Cantillation: U+0591–U+05AF; paseq U+05C0; sof pasuq U+05C3
    return re.sub(r'[֑-֯׀׃]', '', s)

def clean_html(s):
    """Strip HTML tags and common HTML entities."""
    s = re.sub(r'<[^>]+>', '', s)
    for ent, ch in [('&thinsp;', ' '), ('&nbsp;', ' '), ('&amp;', '&'),
                    ('&lt;', '<'), ('&gt;', '>'), ('&quot;', '"')]:
        s = s.replace(ent, ch)
    return re.sub(r'\s+', ' ', s).strip()

def clean_verse(s):
    """Full clean: strip HTML, cantillation, section markers."""
    s = clean_html(s)
    s = strip_cantillation(s)
    # Remove parasha/section markers like {פ} {ס}
    s = re.sub(r'\{[פס]\}', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def bare(s):
    """Strip everything except Hebrew consonants (for matching)."""
    s = clean_html(s)
    return re.sub(r'[^א-ת]', '', s)

def tokenize(verse_text):
    """
    Split verse into display tokens. Split on spaces AND on maqqef (U+05BE ־)
    so words joined by maqqef become separate queryable tokens.
    Filter out empty strings and section markers.
    """
    raw = re.split(r'[\s־]+', verse_text)
    return [t for t in raw if t and not re.match(r'^\{[פס]\}$', t)]

# ── Fetch from Sefaria ────────────────────────────────────────────────────────

def fetch_verse(sefaria_ref):
    """
    Return (hebrew_display, english_text) for a single verse.
    sefaria_ref format: "Book.Chapter.Verse"
    """
    url = SEFARIA.format(sefaria_ref)
    resp = requests.get(url, headers=UA, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    # Verse index: last component of ref is the verse number (1-based → 0-indexed)
    verse_num = int(sefaria_ref.split('.')[-1]) - 1

    he_raw   = data.get('he', '')
    text_raw = data.get('text', '')

    # Sefaria returns the whole chapter as a list; pick our verse
    if isinstance(he_raw, list):
        he_raw = he_raw[verse_num] if verse_num < len(he_raw) else ''
    if isinstance(text_raw, list):
        text_raw = text_raw[verse_num] if verse_num < len(text_raw) else ''

    he_display = clean_verse(he_raw)

    # Clean English: strip footnotes entirely, join smallcaps words
    en_text = text_raw
    en_text = re.sub(r'<sup[^>]*>.*?</sup>', '', en_text, flags=re.S)   # footnote markers
    en_text = re.sub(r'<i[^>]*>.*?</i>',     '', en_text, flags=re.S)   # footnote text
    en_text = re.sub(r'<(?:small|big)>([^<]+)</(?:small|big)>', r'\1', en_text)  # smallcaps join
    en_text = re.sub(r'<[^>]+>', ' ', en_text)                           # remaining tags
    en_text = re.sub(r'\s+', ' ', en_text).strip()

    return he_display, en_text

# ── Word matching ─────────────────────────────────────────────────────────────

# Single-letter prefixes commonly attached to Hebrew words
_PREFIXES = ('וה', 'בה', 'לה', 'מה', 'ו', 'ב', 'ל', 'ה', 'כ', 'מ', 'ש')

def _stripped_variants(w):
    """Yield w stripped of 0, 1, or 2 leading prefixes."""
    yield w
    for p in _PREFIXES:
        if w.startswith(p) and len(w) > len(p):
            once = w[len(p):]
            yield once
            for p2 in _PREFIXES:
                if once.startswith(p2) and len(once) > len(p2):
                    yield once[len(p2):]

def word_matches(token, quiz_bare):
    """
    Return True if the token's bare consonants match quiz_bare,
    allowing for 1–2 leading prefixes to be stripped.
    For quiz_bare of 3+ chars, also accepts it as a leading substring
    of the stripped form (handles verb suffixes like ך, כם, etc.)
    """
    tb = bare(token)
    for variant in _stripped_variants(tb):
        if variant == quiz_bare:
            return True
        # Accept "quiz + short suffix" (≤3 extra consonants)
        if len(quiz_bare) >= 3 and variant.startswith(quiz_bare) and len(variant) - len(quiz_bare) <= 3:
            return True
    return False

# ── Wrong choices from vocab ──────────────────────────────────────────────────

def load_vocab():
    try:
        return json.loads(VOCAB_FILE.read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {}

def get_wrong_choices(book, correct_answer, vocab, count=3):
    """Pick `count` English definitions from the book's vocab, excluding the answer."""
    candidates = []
    if book in vocab:
        words = vocab[book].get('words', [])
        candidates = [
            w['english'] for w in words
            if w.get('english') and w['english'].lower() != correct_answer.lower()
        ]
        random.shuffle(candidates)

    if len(candidates) < count:
        # Pull from other books as fallback
        for _, bdata in vocab.items():
            for w in bdata.get('words', []):
                eng = w.get('english', '')
                if eng and eng.lower() != correct_answer.lower() and eng not in candidates:
                    candidates.append(eng)
            if len(candidates) >= count * 3:
                break
        random.shuffle(candidates)

    return candidates[:count]

# ── Build a single question ───────────────────────────────────────────────────

def build_question(sefaria_ref, book, quiz_bare, answer, vocab):
    """
    Fetch the verse, locate the quiz word, return a question dict.
    Returns None if the word can't be found in the verse.
    """
    ref_display = sefaria_ref.replace('.', ' ').replace(' ', ' ', 1)  # e.g. "Genesis 1:1"
    parts       = sefaria_ref.split('.')
    ref_display = f"{parts[0]} {parts[1]}:{parts[2]}"

    print(f"  {ref_display:25s}  quiz={quiz_bare:10s}", end='  ', flush=True)

    he_text, en_text = fetch_verse(sefaria_ref)

    if not he_text:
        print("✗  empty verse")
        return None

    tokens = tokenize(he_text)

    # Find first token whose bare consonants match quiz_bare
    found_idx  = None
    found_word = None
    for i, tok in enumerate(tokens):
        if word_matches(tok, quiz_bare):
            found_idx  = i
            found_word = tok
            break

    if found_idx is None:
        print(f"✗  '{quiz_bare}' not found in: {' '.join(bare(t) for t in tokens)}")
        return None

    wrong_choices = get_wrong_choices(book, answer, vocab)

    print(f"✓  word='{found_word}'  answer='{answer}'")

    return {
        "ref":           ref_display,
        "sefaria_ref":   sefaria_ref,
        "book":          book,
        "hebrew_text":   he_text,
        "english_text":  en_text,
        "words":         tokens,
        "quiz_word_idx": found_idx,
        "quiz_word":     found_word,
        "answer":        answer,
        "wrong_choices": wrong_choices,
    }

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build pasuk_questions.json from Sefaria")
    parser.add_argument("--refresh", action="store_true", help="Rebuild all questions from scratch")
    args = parser.parse_args()

    vocab = load_vocab()

    # Load existing questions (skip already-built ones unless --refresh)
    questions = []
    if not args.refresh and OUT_FILE.exists():
        questions = json.loads(OUT_FILE.read_text(encoding='utf-8'))
        print(f"Loaded {len(questions)} existing questions from {OUT_FILE.name}")

    # Build a set of already-done (ref, quiz_bare) pairs
    done = {(q['sefaria_ref'], bare(q['quiz_word'])) for q in questions}

    added = 0
    skipped = 0

    print(f"\nProcessing {len(PASUKIM)} pasukim…\n")

    for sefaria_ref, book, quiz_bare, answer in PASUKIM:
        key = (sefaria_ref, quiz_bare)
        if key in done:
            print(f"  {'  skip':25s}  {sefaria_ref} [{quiz_bare}]")
            skipped += 1
            continue

        q = build_question(sefaria_ref, book, quiz_bare, answer, vocab)
        if q:
            questions.append(q)
            done.add(key)
            added += 1
            # Save after each success so progress isn't lost
            OUT_FILE.write_text(
                json.dumps(questions, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )

        time.sleep(0.4)   # be polite to Sefaria

    print(f"\n{'─'*52}")
    print(f"Done. {len(questions)} total questions in {OUT_FILE.name}")
    print(f"  {added} new  |  {skipped} skipped")

    # Print a preview of all questions
    print(f"\nPreview:")
    for q in questions:
        print(f"  {q['ref']:20s}  {q['quiz_word']:20s}  → {q['answer']}")

if __name__ == "__main__":
    main()
