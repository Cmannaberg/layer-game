#!/usr/bin/env python3
"""
vocab_filter.py
Removes proper nouns, prepositions, and conjunctions from hebrew_vocab.json.

Usage:
    python3 vocab_filter.py           # preview only — shows what would be removed
    python3 vocab_filter.py --apply   # make the changes (backs up original first)
"""

import argparse, json, re, shutil
from pathlib import Path

VOCAB_FILE = Path(__file__).parent / "hebrew_vocab.json"
BACKUP_FILE = Path(__file__).parent / "hebrew_vocab.backup.json"

# ── Hardcoded list of Hebrew prepositions and conjunctions ────────────────────
# Strip nikkud for matching (consonants only)

def consonants(s):
    """Return only Hebrew consonants — strip nikkud, trop, everything else."""
    return re.sub(r'[^א-ת]', '', s)

# Known prepositions, conjunctions, and particles to always remove.
# Match on the FULL Hebrew word (with nikkud) to avoid false positives
# where the same consonants spell a different vocabulary word.
# e.g. אֵל = "god" (keep) vs אֶל = "to/toward" (remove) — same consonants, different nikkud
FUNCTION_WORDS_EXACT = {
    # Conjunctions
    'כִּי',    # that, because, for, when, if
    'אֲשֶׁר',  # that, which, who  (NOT אֶשֶׁר = happiness)
    'אִם',    # if, whether
    'פֶּן',    # lest
    # Prepositions
    'עַל',    # on, over, upon, about
    'אֶל',    # to, toward, into  (NOT אֵל = god)
    'מִן',    # from, out of
    'עִם',    # with  (NOT עַם = nation/people)
    'אֵת',    # direct object marker
    'אֶת',    # direct object marker (alternate spelling)
    'בֵּין',   # between, among
    'תַּחַת',  # under, beneath, instead of
    'לִפְנֵי', # before, in front of
    'אַחֲרֵי', # after, behind
    # Common words too basic / too frequent to quiz
    'הָיָה',   # to be, become, come to pass, exist, happen
    'אָמַר',   # to say, speak, utter
    'עָשָׂה',  # to do, fashion, accomplish, make
    'בּוֹא',   # to go in, enter, come, go
    'דָבַר',   # to speak, declare, converse, command
    'שׂוּם',   # to put, place, set / no, nothing
    'אִישׁ',   # man
    'אָב',    # father
    'בֵּן',   # son, grandson, child
    'בַּת',   # daughter
    'אֲדָמָה', # ground, land
    'אַיִל',  # ram
    'אָחוֹר',  # the back side, the rear
    'יָם',    # sea
    'יוֹם',   # day, time, year
    'שָׁמָּה',  # there, thither
}

# ── Proper noun detection ─────────────────────────────────────────────────────
# English words that are always legitimate vocabulary (not proper nouns)
# even though they start with a capital letter in some definitions
NOT_PROPER = {
    'god', 'lord', 'the lord', 'i am', 'i will be',
}

# English words/phrases that signal a proper noun definition
PROPER_NOUN_SIGNALS = [
    # Peoples / ethnic groups
    'amorite', 'canaanite', 'israelite', 'philistine', 'aramean',
    'moabite', 'edomite', 'ammonite', 'hittite', 'jebusite',
    'chaldean', 'assyrian', 'babylonian', 'egyptian', 'cushite',
    'midianite', 'amalekite', 'perizzite', 'hivite',
    # Specific named months / places
    'adar', 'nisan', 'tishri', 'sivan',
    # Generic proper-noun markers
    ' = "',          # Sefaria often writes  Amorite = "a sayer"
]

def is_proper_noun(word):
    """Return True if the word looks like a proper noun."""
    eng = word.get('english', '').strip()
    if not eng:
        return False
    eng_lower = eng.lower()

    # Check against known signals
    for signal in PROPER_NOUN_SIGNALS:
        if signal in eng_lower:
            return True

    # Capitalized first word that isn't a known-good vocabulary word
    first = re.split(r'[,;/]', eng)[0].strip()
    if first and first[0].isupper():
        if first.lower() not in NOT_PROPER:
            # Extra check: if it's a single capitalized name (no spaces or
            # only "of/the" after), flag it
            words = first.split()
            if len(words) == 1 or (len(words) == 2 and words[1].lower() in ('of','the','a')):
                return True

    return False

def is_function_word(word):
    """Return True if the word is a preposition or conjunction."""
    he = word.get('hebrew', '').strip()
    return he in FUNCTION_WORDS_EXACT

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Filter proper nouns and function words from hebrew_vocab.json")
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is preview only)")
    args = parser.parse_args()

    with open(VOCAB_FILE, encoding='utf-8') as f:
        vocab = json.load(f)

    removed_proper   = []
    removed_function = []
    total_before     = 0
    total_after      = 0

    new_vocab = {}

    for book, bdata in vocab.items():
        words_in  = bdata['words']
        words_out = []

        for w in words_in:
            total_before += 1
            if is_proper_noun(w):
                removed_proper.append((w['hebrew'], w.get('english',''), book))
            elif is_function_word(w):
                removed_function.append((w['hebrew'], w.get('english',''), book))
            else:
                words_out.append(w)
                total_after += 1

        new_vocab[book] = {**bdata, 'words': words_out}

    # ── Report ────────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  VOCAB FILTER — PREVIEW")
    print("=" * 60)

    print(f"\n📌 PREPOSITIONS / CONJUNCTIONS to remove ({len(removed_function)}):")
    if removed_function:
        seen = set()
        for he, en, book in removed_function:
            key = consonants(he)
            if key not in seen:
                seen.add(key)
                print(f"   {he:22s}  {en}")
        print(f"   (appears in {len(removed_function)} book entries total)")
    else:
        print("   none found")

    print(f"\n🏷  PROPER NOUNS to remove ({len(removed_proper)}):")
    if removed_proper:
        for he, en, book in removed_proper:
            print(f"   {he:22s}  {en}  [{book}]")
    else:
        print("   none found")

    total_removed = len(removed_proper) + len(removed_function)
    print()
    print(f"  Words before : {total_before}")
    print(f"  Words removed: {total_removed}")
    print(f"  Words after  : {total_after}")
    print()

    if not args.apply:
        print("─" * 60)
        print("  This was a PREVIEW only. No files were changed.")
        print("  To apply: python3 vocab_filter.py --apply")
        print("─" * 60)
        return

    # ── Apply ─────────────────────────────────────────────────────────────────
    shutil.copy(VOCAB_FILE, BACKUP_FILE)
    print(f"  Backup saved → {BACKUP_FILE.name}")

    with open(VOCAB_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_vocab, f, ensure_ascii=False, indent=2)

    print(f"  {VOCAB_FILE.name} updated — {total_removed} words removed.")
    print()
    print("  If anything looks wrong, restore with:")
    print(f"    cp {BACKUP_FILE} {VOCAB_FILE}")
    print()

if __name__ == "__main__":
    main()
