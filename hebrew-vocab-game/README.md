# Hebrew Vocab Challenge

A Biblical Hebrew vocabulary game for classroom use. Students pick a book of Tanach,
get tested on the 10 most frequent words, and compete on a shared leaderboard.

## Setup

```bash
pip install -r requirements.txt
```

## Build vocabulary data

```bash
python3 hebrew_vocab_builder.py --section Torah      # build one section
python3 hebrew_vocab_builder.py --book Genesis       # build one book
```

## Run the game server

```bash
python3 hebrew_vocab_app.py
```

Open `http://localhost:5050` in a browser.

**Classroom use:** The server runs on your Mac and students connect via your local IP:
```bash
ipconfig getifaddr en0   # find your IP
```
Write `http://[your-ip]:5050` on the board. Students open it in Chrome on Chromebooks.

## Generate a dictionary

```bash
python3 hebrew_vocab_dict.py    # outputs hebrew_vocab_dictionary.html
```

## Files

| File | Purpose |
|------|---------|
| `hebrew_vocab_app.py` | Flask game server |
| `hebrew_vocab_builder.py` | Builds vocab JSON from Sefaria API |
| `hebrew_vocab_dict.py` | Exports vocab as an HTML dictionary |
| `hebrew_vocab.json` | Generated vocabulary data (committed) |
| `players.json` | Leaderboard scores — local only, not committed |
