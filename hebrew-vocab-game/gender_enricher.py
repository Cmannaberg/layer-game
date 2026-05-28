#!/usr/bin/env python3
"""
gender_enricher.py
Adds a 'gender' field to every word entry in hebrew_vocab.json
by looking up each word in the Sefaria lexicon API.

Gender values stored:
  "m"   — masculine noun
  "f"   — feminine noun
  "mf"  — used as both genders in the Bible
  null  — verb, adjective, adverb, or could not be determined

Run:
  python3 gender_enricher.py            # enrich only words missing gender
  python3 gender_enricher.py --refresh  # re-fetch everything from scratch
"""

import argparse, json, re, time
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

VOCAB_FILE = Path(__file__).parent / "hebrew_vocab.json"
UA         = {"User-Agent": "hebrew-vocab-game/1.0"}
API_URL    = "https://www.sefaria.org/api/words/{}?lookup_ref=Genesis+1:1&with_links=0"

# ── Gender detection ──────────────────────────────────────────────────────────

# Patterns that signal masculine or feminine in Sefaria morphology strings
_MASC_RE = re.compile(r'\bn-m\b|(?<!\w)m\.(?!\w)|m\.n\.|m\. pl\.|masculine', re.I)
_FEM_RE  = re.compile(r'\bn-f\b|(?<!\w)f\.(?!\w)|f\.n\.|feminine', re.I)

def fetch_gender(hebrew_word):
    """
    Call the Sefaria lexicon API and return "m", "f", "mf", or None.
    Returns None for verbs, adjectives, or words not found.
    """
    try:
        url  = API_URL.format(requests.utils.quote(hebrew_word))
        resp = requests.get(url, headers=UA, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not isinstance(data, list) or not data:
            return None

        has_m = False
        has_f = False

        for entry in data:
            content = entry.get("content", {})
            if not isinstance(content, dict):
                continue
            morph = content.get("morphology", "")
            if not morph:
                continue
            if _MASC_RE.search(morph):
                has_m = True
            if _FEM_RE.search(morph):
                has_f = True

        if has_m and has_f:
            return "mf"
        if has_m:
            return "m"
        if has_f:
            return "f"
        return None

    except Exception:
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Add gender field to hebrew_vocab.json")
    parser.add_argument("--refresh", action="store_true",
                        help="Re-fetch gender for all words, even those already tagged")
    args = parser.parse_args()

    with open(VOCAB_FILE, encoding="utf-8") as f:
        vocab = json.load(f)

    # Count how many words need tagging
    total   = sum(len(b["words"]) for b in vocab.values())
    to_do   = sum(
        1 for b in vocab.values()
        for w in b["words"]
        if args.refresh or "gender" not in w
    )

    print(f"\nWords in vocab : {total}")
    print(f"Words to tag   : {to_do}")
    print(f"(Already tagged: {total - to_do})\n")

    done = 0
    hits = {"m": 0, "f": 0, "mf": 0, None: 0}

    # Cache so we don't call the API twice for the same Hebrew word
    cache = {}

    for book, bdata in vocab.items():
        book_changed = False
        for w in bdata["words"]:
            if not args.refresh and "gender" in w:
                continue

            he = w["hebrew"]
            if he not in cache:
                cache[he] = fetch_gender(he)
                time.sleep(0.35)   # be polite to Sefaria

            gender = cache[he]
            w["gender"] = gender
            hits[gender] += 1
            done += 1
            book_changed = True

            tag = gender if gender else "—"
            print(f"  [{done:3d}/{to_do}] {he:22s}  {tag:3s}  {w['english'][:45]}")

        # Save after each book so progress isn't lost if interrupted
        if book_changed:
            with open(VOCAB_FILE, "w", encoding="utf-8") as f:
                json.dump(vocab, f, ensure_ascii=False, indent=2)

    print(f"\n{'─'*52}")
    print(f"Done.  {done} words tagged.")
    print(f"  Masculine (m) : {hits['m']}")
    print(f"  Feminine  (f) : {hits['f']}")
    print(f"  Both     (mf) : {hits['mf']}")
    print(f"  Unknown   (—) : {hits[None]}")
    print()

if __name__ == "__main__":
    main()
