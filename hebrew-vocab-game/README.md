# Hebrew Vocab Challenge ✡

A Biblical Hebrew vocabulary game for classroom use. Students pick a book of Tanach,
are tested on the 10 most frequent words via multiple choice, and compete on a
shared year-long leaderboard.

**→ See [WORKFLOW.md](WORKFLOW.md) for complete setup and day-to-day instructions.**

---

## Quick Start

```bash
cd ~/layer-game/hebrew-vocab-game
source myenv/bin/activate
python3 hebrew_vocab_app.py
```

Open `http://localhost:5050` — or share your local IP with students on Chromebooks.

## Features

- Pick any book of Tanach (Torah, Nevi'im, Ketuvim)
- Hebrew → English or English → Hebrew multiple choice
- Bonus fill-in-the-blank round for scores of 8/10 or higher (+50 points)
- Persistent leaderboard across all class sessions
- Hebrew word lookup tool at `/lookup`
- Export a printable dictionary with `python3 hebrew_vocab_dict.py`
