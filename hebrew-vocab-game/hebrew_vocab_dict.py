#!/usr/bin/env python3
"""
Generate a Hebrew-English dictionary HTML file from hebrew_vocab.json.
Words are deduplicated across books and sorted alphabetically in Hebrew.
Run: python3 hebrew_vocab_dict.py
Output: hebrew_vocab_dictionary.html
"""

import json
from pathlib import Path

SECTION_ORDER = ["Torah", "Nevi'im", "Ketuvim"]
IN_FILE  = "hebrew_vocab.json"
OUT_FILE = "hebrew_vocab_dictionary.html"


def pos_label(english):
    return "verb" if english.strip().startswith("to ") else "noun"


def build_combined(vocab):
    """Merge all books into one dict keyed by Hebrew headword."""
    combined = {}
    for book_id, data in vocab.items():
        short = data["display_name"].split("/")[0].strip()
        for word in data.get("words", []):
            hw = word["hebrew"]
            if hw not in combined:
                combined[hw] = {
                    "english":    word["english"],
                    "pos":        pos_label(word["english"]),
                    "books":      [],
                    "total_freq": 0,
                }
            combined[hw]["books"].append((short, word["frequency"]))
            combined[hw]["total_freq"] += word["frequency"]

    # Sort alphabetically by Hebrew (Unicode order matches alef-bet order)
    return sorted(combined.items(), key=lambda x: x[0])


def letter_group(hebrew_word):
    """Return the first Hebrew letter for grouping."""
    for ch in hebrew_word:
        if "א" <= ch <= "ת":
            return ch
    return hebrew_word[0]


def build_alpha_entries(word_list):
    """Build A-Z style grouped HTML entries."""
    html = ""
    current_letter = None

    for hw, data in word_list:
        letter = letter_group(hw)
        if letter != current_letter:
            if current_letter is not None:
                html += "</div>"   # close previous letter group
            current_letter = letter
            html += f"""
            <div class="letter-group">
              <div class="letter-heading" dir="rtl">{letter}</div>"""

        book_tags = "".join(
            f'<span class="book-tag">{b} <span class="tag-freq">{f:,}×</span></span>'
            for b, f in data["books"]
        )
        html += f"""
          <div class="entry">
            <div class="entry-hebrew" dir="rtl">{hw}</div>
            <div class="entry-body">
              <span class="entry-pos">{data['pos']}</span>
              <span class="entry-def">{data['english']}</span>
              <div class="entry-books">{book_tags}</div>
            </div>
          </div>"""

    if current_letter is not None:
        html += "</div>"  # close last letter group
    return html


def main():
    vocab     = json.loads(Path(IN_FILE).read_text(encoding="utf-8"))
    word_list = build_combined(vocab)
    entries   = build_alpha_entries(word_list)

    total_books   = len(vocab)
    total_entries = len(word_list)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Biblical Hebrew Vocabulary Dictionary</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@400;700;900&family=Crimson+Pro:ital,wght@0,400;0,600;1,400&family=Nunito:wght@600;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --blue:  #1a3a6b;
      --gold:  #b8860b;
      --light: #faf7f2;
      --rule:  #d4c9b0;
      --text:  #1a1a1a;
      --muted: #6b6b6b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Crimson Pro', Georgia, serif;
      background: var(--light);
      color: var(--text);
      font-size: 17px;
      line-height: 1.5;
    }}

    /* ── TITLE PAGE ── */
    .title-page {{
      text-align: center;
      padding: 80px 40px 60px;
      border-bottom: 3px double var(--rule);
      margin-bottom: 48px;
    }}
    .title-ornament {{ font-size: 2.8rem; color: var(--gold); margin-bottom: 16px; }}
    .title-main {{
      font-family: 'Frank Ruhl Libre', serif;
      font-size: 2.6rem;
      font-weight: 900;
      color: var(--blue);
      line-height: 1.2;
      margin-bottom: 8px;
    }}
    .title-hebrew {{
      font-family: 'Frank Ruhl Libre', serif;
      font-size: 2rem;
      font-weight: 700;
      color: var(--gold);
      direction: rtl;
      margin-bottom: 20px;
    }}
    .title-sub {{ color: var(--muted); font-style: italic; font-size: 1rem; }}
    .title-stats {{
      margin-top: 24px;
      display: inline-flex;
      gap: 32px;
      border-top: 1px solid var(--rule);
      border-bottom: 1px solid var(--rule);
      padding: 12px 32px;
      color: var(--muted);
      font-size: .9rem;
    }}
    .title-stats strong {{ color: var(--blue); font-family: 'Nunito', sans-serif; }}

    /* ── LAYOUT ── */
    .page {{ max-width: 900px; margin: 0 auto; padding: 0 32px 80px; }}

    /* ── LETTER GROUPS ── */
    .letter-group {{ margin-bottom: 32px; }}
    .letter-heading {{
      font-family: 'Frank Ruhl Libre', serif;
      font-size: 2.2rem;
      font-weight: 900;
      color: var(--blue);
      border-bottom: 2px solid var(--blue);
      padding-bottom: 4px;
      margin-bottom: 12px;
    }}

    /* ── DICTIONARY ENTRIES ── */
    .entry {{
      display: flex;
      align-items: flex-start;
      gap: 14px;
      padding: 9px 0;
      border-bottom: 1px solid var(--rule);
    }}
    .entry:last-child {{ border-bottom: none; }}
    .entry-hebrew {{
      font-family: 'Frank Ruhl Libre', serif;
      font-size: 1.55rem;
      font-weight: 700;
      color: var(--blue);
      min-width: 110px;
      text-align: right;
      flex-shrink: 0;
      padding-top: 2px;
    }}
    .entry-body {{ flex: 1; font-size: .93rem; line-height: 1.5; }}
    .entry-pos {{
      font-style: italic;
      color: var(--muted);
      font-size: .8rem;
      margin-right: 5px;
    }}
    .entry-def {{ color: var(--text); font-weight: 600; }}
    .entry-books {{
      margin-top: 4px;
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }}
    .book-tag {{
      background: #e8e0d0;
      border-radius: 4px;
      padding: 1px 7px;
      font-size: .75rem;
      font-family: 'Nunito', sans-serif;
      color: var(--muted);
      font-weight: 600;
    }}
    .tag-freq {{ color: var(--blue); font-weight: 800; }}

    /* ── PRINT ── */
    @media print {{
      body {{ background: white; font-size: 11pt; }}
      .title-page {{ padding: 40px 20px 30px; }}
      .page {{ padding: 0 20px 40px; columns: 2; column-gap: 32px; }}
      .letter-group {{ break-inside: avoid-column; }}
      .entry {{ padding: 5px 0; }}
    }}
  </style>
</head>
<body>

<div class="title-page">
  <div class="title-ornament">✡</div>
  <div class="title-main">Biblical Hebrew<br>Vocabulary Dictionary</div>
  <div class="title-hebrew">מילון עברי-אנגלי</div>
  <div class="title-sub">Most Frequent Words by Book of Tanach · Based on Sefaria texts</div>
  <div class="title-stats">
    <span><strong>{total_books}</strong> books</span>
    <span><strong>{total_entries}</strong> unique words</span>
  </div>
</div>

<div class="page">
  {entries}
</div>

</body>
</html>"""

    Path(OUT_FILE).write_text(html, encoding="utf-8")
    print(f"Written: {OUT_FILE}  ({total_entries} unique words from {total_books} books)")


if __name__ == "__main__":
    main()
