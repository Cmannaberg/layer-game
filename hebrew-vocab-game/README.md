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

The server prints your WiFi URL and a **scannable QR code** at startup.
Students on the same WiFi point their phone camera at it — no typing needed.

## Features

- **Pasuk Challenge** — famous Bible verses with one word highlighted; student translates it from 4 choices; English verse revealed after answering
- Pick any book of Tanach (Torah, Nevi'im, Ketuvim) for word-frequency vocab drill
- Hebrew → English or English → Hebrew multiple choice
- Bonus fill-in-the-blank round for scores of 8/10 or higher (+50 points)
- Persistent year-long leaderboard shared across all devices
- Multi-device: students join via QR code on phones, tablets, or Chromebooks
- Hebrew word lookup tool at `/lookup`
- Export a printable dictionary with `python3 hebrew_vocab_dict.py`
