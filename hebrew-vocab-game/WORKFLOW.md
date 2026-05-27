# Hebrew Vocab Challenge — Workflow Guide

---

## One-Time Setup (do this once)

```bash
# Clone the repo to your home directory
cd ~
git clone https://github.com/Cmannaberg/layer-game.git

# Go into the game folder
cd ~/layer-game/hebrew-vocab-game

# Create and activate a Python virtual environment
python3 -m venv myenv
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Every Day (classroom use)

```bash
# 1. Go to the game folder
cd ~/layer-game/hebrew-vocab-game

# 2. Activate Python environment
source myenv/bin/activate

# 3. Start the server
python3 hebrew_vocab_app.py
```

The terminal will print something like:

```
====================================================
  Hebrew Vocab Game — server starting
====================================================
  This Mac   :  http://localhost:5050/vocab
  WiFi URL   :  http://10.10.2.45:5050/vocab

  Share that URL — or scan this QR code:

▄▄▄▄▄▄▄ ▄ ▄  ...
...
====================================================
```

**Point your phone camera at the QR code** — tap the link and the game opens instantly.
Students on Chromebooks can type the WiFi URL shown in the banner.

Leave the Terminal window open for the entire class.
To stop the server: press **Ctrl+C** in Terminal (don't just close the window —
that leaves the server running and causes a "port already in use" error next time).

> **Note:** Your Mac's local IP can change when it reconnects to WiFi.
> The banner always shows the current IP automatically — no need to look it up.

**WiFi requirements:**
- Your Mac and students' devices must be on the **same WiFi network**
- Works well on home WiFi and most office/shop networks
- Many school and public WiFi networks block device-to-device traffic (called
  "client isolation") — if students can't connect, switch to your Mac's
  Personal Hotspot instead (System Settings → General → Sharing → Internet Sharing)

---

## Pasuk Challenge

The Pasuk Challenge shows a complete Hebrew verse with one word highlighted in
gold. Students pick the correct English translation from four choices. After
answering, the full English verse is revealed.

**How students access it:**
On the book-selection screen, there's a blue "📜 Pasuk Challenge" banner at the
top. Tap it to start — no book selection needed.

**What's in the question pool:**
22 famous verses spanning all three sections of Tanach — Bereshit 1:1, the
Shema, "Love your neighbor", the Priestly Blessing, Psalm 23, "Be strong and
courageous", Isaiah's Keddushah, and more. Each session draws 7 random
questions. Scores go on the same year-long leaderboard.

**Adding more verses:**
Open `pasuk_builder.py` and add an entry to the `PASUKIM` list:

```python
("Book.Chapter.Verse", "Book", "consonants-as-in-verse", "English answer"),
# e.g.
("Genesis.15.1",  "Genesis",  "תירא",  "fear, be afraid"),
```

Then re-run the builder — it skips verses already in the file:

```bash
cd ~/layer-game/hebrew-vocab-game
source myenv/bin/activate
python3 pasuk_builder.py
```

---

## Adding New Books to the Vocab Data

```bash
cd ~/layer-game/hebrew-vocab-game
source myenv/bin/activate

# Add a single book
python3 hebrew_vocab_builder.py --book Exodus

# Add a whole section
python3 hebrew_vocab_builder.py --section "Nevi'im"
python3 hebrew_vocab_builder.py --section Ketuvim

# Add all remaining books
python3 hebrew_vocab_builder.py
```

The builder skips books already in `hebrew_vocab.json`, so it's safe to re-run.
Each book takes about 5–10 minutes to build.

---

## Generating the Dictionary

```bash
cd ~/layer-game/hebrew-vocab-game
source myenv/bin/activate
python3 hebrew_vocab_dict.py
```

Opens `hebrew_vocab_dictionary.html` in Finder — double-click to view in browser.
Regenerate any time you add new books.

---

## Editing Definitions and Removing Words

```bash
code ~/layer-game/hebrew-vocab-game/hebrew_vocab.json
```

First, auto-format the file so it's easy to read: `Shift+Option+F`

Each word entry looks like this:
```json
{
  "hebrew": "אֶרֶץ",
  "english": "land, earth",
  "frequency": 304
}
```

**Fix a definition** — edit the `"english"` value and save.

**Remove a word** — delete the entire `{ }` block for that entry,
including the comma after the previous entry. VS Code will underline
in red if the JSON structure is broken.

When done, push your changes to GitHub:
```bash
cd ~/layer-game
git add hebrew-vocab-game/hebrew_vocab.json
git commit -m "clean up vocab definitions"
git push
```

---

## Resetting the Leaderboard

```bash
rm ~/layer-game/hebrew-vocab-game/players.json
```

Do this at the start of a new semester. Scores start fresh.
The file is recreated automatically when the first student plays.

---

## Saving Your Changes to GitHub

After editing any files (definitions, templates, scripts):

```bash
cd ~/layer-game
git add hebrew-vocab-game/
git commit -m "describe what you changed"
git push
```

`players.json` is excluded automatically — student scores stay local only.

---

## Getting Updates on Another Mac

If you ever set this up on a second machine:

```bash
cd ~/layer-game
git pull
```

---

## Planned Future Features

Ideas discussed for future development, roughly in order of priority:

**Difficulty levels**
- Level 1 (current): words ranked 1–10 by frequency in each book
- Level 2: words ranked 11–20 (already in `hebrew_vocab.json`, just unused)
- Level 3: fill-in-the-blank for all 10 words, not just the bonus round

**Bible text passage questions**
- Show an actual pasuk (verse) from Sefaria with one word highlighted
- Student translates the highlighted word in context
- Much closer to real Torah reading skill
- Sefaria API already supports this — same API already used in the project

**More challenge types**
- Matching (connect Hebrew column to English column)
- Hear the word / audio pronunciation
- Root identification (given an inflected form, identify the shoresh)

**Root identification (Shoresh)**
- Show a long inflected word from the Bible (e.g. וַיִּכְתְּבֵהוּ)
- Student identifies the 3-letter root (shoresh) from multiple choice
- Then defines the root
- Teaches the most important Biblical Hebrew skill

**Prefix and suffix morphology**
- Show a root word, then add a prefix or suffix (e.g. ב, ל, ו, ים, ות, ה)
- Student guesses the new meaning or grammatical form
- Covers: definite article, prepositions, conjunctions, plurals, gender endings
- Builds reading skill by teaching how words change in context

**Noun gender**
- Show a Hebrew noun, student guesses masculine or feminine
- Hint mode: teach the patterns (ה- and ת- endings are usually feminine)
- Could also include dual and plural forms

**Classroom management**
- Reset leaderboard at start of each semester: `rm players.json`
- Per-class leaderboards (multiple `players_period1.json` etc.)

---

## File Map

| File | What it does |
|------|-------------|
| `hebrew_vocab_app.py` | Runs the game server; prints WiFi URL + QR code at startup |
| `hebrew_vocab_builder.py` | Fetches vocab from Sefaria API, builds JSON |
| `hebrew_vocab_dict.py` | Exports vocab as a printable HTML dictionary |
| `hebrew_vocab.json` | All vocabulary data — edit definitions here |
| `pasuk_builder.py` | Fetches famous verses from Sefaria API, builds pasuk question data |
| `pasuk_questions.json` | Pasuk Challenge question pool — 22 famous verses with quiz data |
| `players.json` | Leaderboard scores — local only, not on GitHub |
| `templates/vocab/index.html` | The game UI (vocab drill + Pasuk Challenge) |
| `templates/vocab/lookup.html` | Hebrew word lookup tool |
| `requirements.txt` | Python package list |
