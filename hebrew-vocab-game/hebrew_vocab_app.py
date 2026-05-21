#!/usr/bin/env python3
"""
Biblical Hebrew Vocabulary Game — Flask app.
Run: python3 hebrew_vocab_app.py
Then open: http://localhost:5050/vocab
"""

import json, os, random
from datetime import date
from flask import Flask, render_template, jsonify, redirect, request

app = Flask(__name__)
VOCAB_FILE   = os.path.join(os.path.dirname(__file__), "hebrew_vocab.json")
PLAYERS_FILE = os.path.join(os.path.dirname(__file__), "players.json")
SECTION_ORDER = ["Torah", "Nevi'im", "Ketuvim"]


@app.route("/")
def root():
    return redirect("/vocab")


# ── Players / leaderboard ────────────────────────────────────────────────────

def load_players():
    try:
        with open(PLAYERS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        # Migrate old flat format {"name": score} to new format
        migrated = {}
        for name, val in data.items():
            if isinstance(val, int) or isinstance(val, float):
                migrated[name] = {"total": int(val), "played": {}}
            else:
                migrated[name] = val
        return migrated
    except FileNotFoundError:
        return {}

def save_players(players):
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=2)

def today():
    return date.today().isoformat()   # e.g. "2026-05-21"


@app.route("/vocab/api/leaderboard")
def api_leaderboard():
    players = load_players()
    board = sorted(
        [{"name": k, "score": v["total"]} for k, v in players.items()],
        key=lambda x: x["score"], reverse=True
    )
    return jsonify(board)


@app.route("/vocab/api/score", methods=["POST"])
def api_add_score():
    data    = request.get_json()
    name    = (data.get("name") or "").strip()
    points  = int(data.get("points", 0))
    book_id = (data.get("book_id") or "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400

    players = load_players()
    if name not in players:
        players[name] = {"total": 0, "played": {}}

    player   = players[name]
    today_str = today()

    # Clean up old dates to keep the file small
    player["played"] = {k: v for k, v in player["played"].items() if k == today_str}

    already_played = book_id in player["played"].get(today_str, [])

    if already_played:
        save_players(players)
        return jsonify({
            "scored":  False,
            "total":   player["total"],
            "message": f"You already earned points for {book_id} today — great practice though!",
        })

    # Award points and record the play
    player["total"] += points
    player["played"].setdefault(today_str, []).append(book_id)
    save_players(players)
    return jsonify({"scored": True, "total": player["total"]})


# ── Vocab ────────────────────────────────────────────────────────────────────

def load_vocab():
    try:
        with open(VOCAB_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


@app.route("/vocab")
def index():
    return render_template("vocab/index.html")


@app.route("/vocab/api/books")
def api_books():
    vocab = load_vocab()
    sections = {s: [] for s in SECTION_ORDER}
    for book_id, data in vocab.items():
        sec = data.get("section", "Torah")
        if sec in sections:
            sections[sec].append({
                "id": book_id,
                "display_name": data["display_name"],
            })
    return jsonify({"sections": sections, "order": SECTION_ORDER})


@app.route("/vocab/api/words/<path:book_id>")
def api_words(book_id):
    vocab = load_vocab()
    if book_id not in vocab:
        return jsonify({"error": "Book not found"}), 404
    words = vocab[book_id]["words"]   # send all words; JS picks 10 randomly
    if len(words) < 3:
        return jsonify({"error": "Not enough words built yet"}), 400
    return jsonify({
        "book_id": book_id,
        "display_name": vocab[book_id]["display_name"],
        "words": words,
    })


# ── Word lookup ──────────────────────────────────────────────────────────────

@app.route("/lookup")
def lookup():
    return render_template("vocab/lookup.html")


@app.route("/lookup/api/<path:word>")
def lookup_api(word):
    import requests as req
    s = req.Session()
    s.headers.update({"User-Agent": "torah-engine/1.0"})
    r = s.get(f"https://www.sefaria.org/api/words/{word}?lookup_ref=Genesis+1:1&with_links=0", timeout=15)
    if r.status_code != 200:
        return jsonify({"error": "Not found"}), 404
    data = r.json()
    if not isinstance(data, list) or not data:
        return jsonify({"error": "No entry found"}), 404

    results = []
    for entry in data:
        content  = entry.get("content", {})
        headword = entry.get("headword", word)
        lexicon  = entry.get("parent_lexicon", "")
        morph    = content.get("morphology", "") if isinstance(content, dict) else ""
        senses   = content.get("senses", [])     if isinstance(content, dict) else []

        def extract_senses(sense_list, depth=0):
            out = []
            for s in sense_list:
                if not isinstance(s, dict):
                    continue
                defn = s.get("definition", "").strip()
                if defn:
                    out.append({"definition": defn, "depth": depth})
                out.extend(extract_senses(s.get("senses", []), depth + 1))
            return out

        results.append({
            "headword":   headword,
            "lexicon":    lexicon,
            "morphology": morph,
            "senses":     extract_senses(senses),
        })

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
