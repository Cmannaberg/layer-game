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

# 4. Find your Mac's IP address (run in a second Terminal tab)
ipconfig getifaddr en0
```

Write `http://[your-ip]:5050` on the board.
Students open that URL in Chrome on their Chromebooks.
Leave the Terminal window open for the entire class.

To stop the server: press `Ctrl+C` in Terminal.

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

## File Map

| File | What it does |
|------|-------------|
| `hebrew_vocab_app.py` | Runs the game server |
| `hebrew_vocab_builder.py` | Fetches vocab from Sefaria API, builds JSON |
| `hebrew_vocab_dict.py` | Exports vocab as a printable HTML dictionary |
| `hebrew_vocab.json` | All vocabulary data — edit definitions here |
| `players.json` | Leaderboard scores — local only, not on GitHub |
| `templates/vocab/index.html` | The game UI |
| `templates/vocab/lookup.html` | Hebrew word lookup tool |
| `requirements.txt` | Python package list |
