#!/usr/bin/env python3
"""
Build Biblical Hebrew vocabulary frequency lists using the Sefaria API.

Usage:
  python3 hebrew_vocab_builder.py                  # build all books
  python3 hebrew_vocab_builder.py --book Genesis   # single book
  python3 hebrew_vocab_builder.py --section Torah  # one section
"""

import json, re, time, argparse
from collections import Counter
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SEFARIA = "https://www.sefaria.org/api"

# Session with automatic retries and a browser-like User-Agent
_session = requests.Session()
_session.headers.update({"User-Agent": "torah-engine-vocab-builder/1.0 (educational project)"})
_retry = Retry(total=4, backoff_factor=1.5,
               status_forcelist=[429, 500, 502, 503, 504],
               allowed_methods=["GET"])
_session.mount("https://", HTTPAdapter(max_retries=_retry))
OUT_FILE = "hebrew_vocab.json"
TOP_N = 20          # words to store per book (game uses 10, extra for wrong answers)
CANDIDATES = 80     # how many frequent words to try before giving up

BOOKS = {
    "Torah": [
        ("Genesis",      "Bereishit / Genesis"),
        ("Exodus",       "Shemot / Exodus"),
        ("Leviticus",    "Vayikra / Leviticus"),
        ("Numbers",      "Bamidbar / Numbers"),
        ("Deuteronomy",  "Devarim / Deuteronomy"),
    ],
    "Nevi'im": [
        ("Joshua",      "Yehoshua / Joshua"),
        ("Judges",      "Shoftim / Judges"),
        ("I Samuel",    "Shmuel I / I Samuel"),
        ("II Samuel",   "Shmuel II / II Samuel"),
        ("I Kings",     "Melachim I / I Kings"),
        ("II Kings",    "Melachim II / II Kings"),
        ("Isaiah",      "Yeshayahu / Isaiah"),
        ("Jeremiah",    "Yirmeyahu / Jeremiah"),
        ("Ezekiel",     "Yechezkel / Ezekiel"),
        ("Hosea",       "Hoshea / Hosea"),
        ("Joel",        "Yoel / Joel"),
        ("Amos",        "Amos"),
        ("Obadiah",     "Ovadiah / Obadiah"),
        ("Jonah",       "Yonah / Jonah"),
        ("Micah",       "Micha / Micah"),
        ("Nahum",       "Nachum / Nahum"),
        ("Habakkuk",    "Chavakuk / Habakkuk"),
        ("Zephaniah",   "Tzefaniah / Zephaniah"),
        ("Haggai",      "Chaggai / Haggai"),
        ("Zechariah",   "Zechariah"),
        ("Malachi",     "Malachi"),
    ],
    "Ketuvim": [
        ("Psalms",        "Tehillim / Psalms"),
        ("Proverbs",      "Mishlei / Proverbs"),
        ("Job",           "Iyov / Job"),
        ("Song of Songs", "Shir HaShirim / Song of Songs"),
        ("Ruth",          "Ruth"),
        ("Lamentations",  "Eichah / Lamentations"),
        ("Ecclesiastes",  "Kohelet / Ecclesiastes"),
        ("Esther",        "Esther"),
        ("Daniel",        "Daniel"),
        ("Ezra",          "Ezra"),
        ("Nehemiah",      "Nehemiah"),
        ("I Chronicles",  "Divrei HaYamim I / I Chronicles"),
        ("II Chronicles", "Divrei HaYamim II / II Chronicles"),
    ],
}

# Words to exclude from the frequency count entirely
SKIP_WORDS = {
    "את",                           # direct object marker
    # Divine names — ultra-frequent but not vocabulary to quiz
    "יהוה", "אלהים", "אלהי", "אל", "אדני", "שדי", "צבאות", "אלה",
}

# BDB morphology prefixes we want to keep (noun and verb only)
KEEP_MORPH = ("n-", "n ", "vb", "v ")   # e.g. "n-f", "n-m", "vb", "v"

DIACRITICS = re.compile(r"[֑-ׇ]")


def strip_nikkud(text):
    return DIACRITICS.sub("", text)

def strip_html(text):
    return re.sub(r"<[^>]+>", "", text)

def get_chapter_count(book_name):
    r = _session.get(f"{SEFARIA}/index/{book_name}", timeout=30)
    r.raise_for_status()
    data = r.json()
    schema = data.get("schema", {})
    lengths = schema.get("lengths", [])
    if lengths:
        return lengths[0]
    # Composite books (e.g. Song of Songs) may nest differently
    nodes = schema.get("nodes", [])
    if nodes and "lengths" in nodes[0]:
        return nodes[0]["lengths"][0]
    return None

def fetch_chapter_words(book_name, chapter):
    url = f"{SEFARIA}/texts/{book_name} {chapter}?lang=he&context=0"
    r = _session.get(url, timeout=30)
    if r.status_code != 200:
        return []
    verses = r.json().get("he", [])
    if isinstance(verses, str):
        verses = [verses]
    words = []
    for verse in verses:
        if isinstance(verse, str):
            clean = strip_nikkud(strip_html(verse))
            words.extend(re.findall(r"[א-ת]+", clean))
    return words

_ABBREV = re.compile(
    r"\(b\.?\s*h\.?\)\s*|pr\.\s*n\.\s*[mf]\.\s*|"
    r"\(pl\.[^)]*\)\s*|\(dual[^)]*\)\s*|\(after[^)]*\)\s*|"
    r"\(relative[^)]*\)\s*|\(plural[^)]*\)\s*|\(inflected[^)]*\)\s*"
)

def _clean(text):
    text = re.sub(r"<[^>]+>", "", text)   # strip HTML
    text = _ABBREV.sub("", text)           # strip BDB abbreviations
    text = re.sub(r"\s+", " ", text)       # collapse whitespace
    text = text.strip().rstrip(".,;")
    # Take only the first definition chunk (before semicolon)
    text = text.split(";")[0].strip()
    return text[:80]

def lookup_definition(word):
    """Return (headword, english_gloss, morphology) or (None, None, None).

    Sefaria BDB response shape:
      [{"headword": "...", "content": {"morphology": "...", "senses": [...]}, ...}]
    headword is the dictionary/citation form with nikud (e.g. אָמַר for "say").
    morphology is a short code: "n-f", "n-m", "vb", "prep", "n-pr", etc.
    """
    url = f"{SEFARIA}/words/{word}?lookup_ref=Genesis+1:1&with_links=0"
    try:
        r = _session.get(url, timeout=15)
        if r.status_code != 200:
            return None, None, None
        data = r.json()
        if not isinstance(data, list) or not data:
            return None, None, None
        for entry in data:
            content = entry.get("content", {})
            if not isinstance(content, dict):
                continue
            headword = entry.get("headword", word)
            morph = content.get("morphology", "")
            senses = content.get("senses", [])
            if senses and isinstance(senses[0], dict):
                raw = senses[0].get("definition", "").strip()
                if raw:
                    gloss = _clean(raw)
                    if gloss:
                        return headword, gloss, morph
        # Fallback: plain string content
        content = data[0].get("content", "")
        headword = data[0].get("headword", word)
        if isinstance(content, str) and content.strip():
            return headword, _clean(content), ""
    except Exception as e:
        print(f"    lookup error for {word}: {e}")
    return None, None, None

def build_book(book_id, display_name, section):
    print(f"\n  {display_name}")
    chapters = get_chapter_count(book_id)
    if not chapters:
        print("    could not determine chapter count — skipping")
        return None
    print(f"    {chapters} chapters")

    all_words = []
    for ch in range(1, chapters + 1):
        all_words.extend(fetch_chapter_words(book_id, ch))
        if ch % 10 == 0:
            print(f"    chapter {ch}/{chapters}")
        time.sleep(0.12)

    print(f"    {len(all_words)} total tokens")
    counter = Counter(w for w in all_words if len(w) >= 2 and w not in SKIP_WORDS)

    results = []
    seen_headwords = set()
    for word, freq in counter.most_common(CANDIDATES):
        if len(results) >= TOP_N:
            break
        print(f"    looking up: {word} ({freq}x)")
        headword, defn, morph = lookup_definition(word)
        time.sleep(0.2)
        if not defn or not headword:
            continue
        # Keep only nouns (n-m, n-f, n-c) and verbs (vb, v); skip proper nouns, prepositions, etc.
        morph_ok = any(morph.startswith(p) for p in KEEP_MORPH) or morph in ("n", "v")
        is_proper = "pr" in morph
        # Verbs often have no morphology field — detect by "to " definition prefix
        if not morph and defn.startswith("to "):
            morph = "v"
        # Extra guard: skip divine names even if BDB tags them as common nouns
        if headword in {"אֱלֹהִים", "יְהֹוָה", "אֲדֹנָי", "שַׁדַּי", "יַהְוֶה"}:
            continue
        if morph_ok and not is_proper and headword not in seen_headwords:
            seen_headwords.add(headword)
            results.append({"hebrew": headword, "english": defn, "frequency": freq})

    return {"display_name": display_name, "section": section, "words": results}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book",    help="Process one book by English name, e.g. Genesis")
    parser.add_argument("--section", help="Process one section: Torah, Nevi'im, or Ketuvim")
    args = parser.parse_args()

    try:
        with open(OUT_FILE, encoding="utf-8") as f:
            vocab = json.load(f)
    except FileNotFoundError:
        vocab = {}

    for section, books in BOOKS.items():
        if args.section and section != args.section:
            continue
        print(f"\n=== {section} ===")
        for book_id, display_name in books:
            if args.book and book_id != args.book:
                continue
            if book_id in vocab and not args.book:
                print(f"  {book_id}: already built — skipping")
                continue
            result = build_book(book_id, display_name, section)
            if result:
                vocab[book_id] = result
                with open(OUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(vocab, f, ensure_ascii=False, indent=2)
                print(f"    saved {len(result['words'])} words")

    print(f"\nDone. {len(vocab)} books in {OUT_FILE}.")

if __name__ == "__main__":
    main()
