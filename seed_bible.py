"""
seed_bible.py
-------------
Seeds the KJV + Strong's JSON into four tables in dependency order:
    1. book           -- 66 rows
    2. chapter        -- 1,189 rows
    3. verse          -- 31,102 rows
    4. versewordlink  -- ~351,804 rows

Requires:
    - Lexicon table already seeded (run seed_lexicon.py first)
    - kjv_strongs.json in the same directory as this script

Usage:
    pip install psycopg2-binary python-dotenv
    python seed_bible.py
"""

import json
import os
import re
import sys
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    sys.exit("Missing dependency: pip install psycopg2-binary")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── Configuration ────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

JSON_FILE = Path(__file__).parent / "kjv_strongs.json"

BATCH_SIZE = 1000

# ─── Book metadata ────────────────────────────────────────────────────────────
# (name, abbreviation, testament, category)

BOOK_METADATA = {
    1:  ("Genesis",          "Gen", "Old", "Law"),
    2:  ("Exodus",           "Exo", "Old", "Law"),
    3:  ("Leviticus",        "Lev", "Old", "Law"),
    4:  ("Numbers",          "Num", "Old", "Law"),
    5:  ("Deuteronomy",      "Deu", "Old", "Law"),
    6:  ("Joshua",           "Jos", "Old", "History"),
    7:  ("Judges",           "Jdg", "Old", "History"),
    8:  ("Ruth",             "Rut", "Old", "History"),
    9:  ("1 Samuel",         "1Sa", "Old", "History"),
    10: ("2 Samuel",         "2Sa", "Old", "History"),
    11: ("1 Kings",          "1Ki", "Old", "History"),
    12: ("2 Kings",          "2Ki", "Old", "History"),
    13: ("1 Chronicles",     "1Ch", "Old", "History"),
    14: ("2 Chronicles",     "2Ch", "Old", "History"),
    15: ("Ezra",             "Ezr", "Old", "History"),
    16: ("Nehemiah",         "Neh", "Old", "History"),
    17: ("Esther",           "Est", "Old", "History"),
    18: ("Job",              "Job", "Old", "Poetry"),
    19: ("Psalms",           "Psa", "Old", "Poetry"),
    20: ("Proverbs",         "Pro", "Old", "Poetry"),
    21: ("Ecclesiastes",     "Ecc", "Old", "Poetry"),
    22: ("Song of Solomon",  "Sol", "Old", "Poetry"),
    23: ("Isaiah",           "Isa", "Old", "Major Prophets"),
    24: ("Jeremiah",         "Jer", "Old", "Major Prophets"),
    25: ("Lamentations",     "Lam", "Old", "Major Prophets"),
    26: ("Ezekiel",          "Eze", "Old", "Major Prophets"),
    27: ("Daniel",           "Dan", "Old", "Major Prophets"),
    28: ("Hosea",            "Hos", "Old", "Other Prophets"),
    29: ("Joel",             "Joe", "Old", "Other Prophets"),
    30: ("Amos",             "Amo", "Old", "Other Prophets"),
    31: ("Obadiah",          "Oba", "Old", "Other Prophets"),
    32: ("Jonah",            "Jon", "Old", "Other Prophets"),
    33: ("Micah",            "Mic", "Old", "Other Prophets"),
    34: ("Nahum",            "Nah", "Old", "Other Prophets"),
    35: ("Habakkuk",         "Hab", "Old", "Other Prophets"),
    36: ("Zephaniah",        "Zep", "Old", "Other Prophets"),
    37: ("Haggai",           "Hag", "Old", "Other Prophets"),
    38: ("Zechariah",        "Zec", "Old", "Other Prophets"),
    39: ("Malachi",          "Mal", "Old", "Other Prophets"),
    40: ("Matthew",          "Mat", "New", "Gospels"),
    41: ("Mark",             "Mar", "New", "Gospels"),
    42: ("Luke",             "Luk", "New", "Gospels"),
    43: ("John",             "Joh", "New", "Gospels"),
    44: ("Acts",             "Act", "New", "History"),
    45: ("Romans",           "Rom", "New", "Pauline Epistles"),
    46: ("1 Corinthians",    "1Co", "New", "Pauline Epistles"),
    47: ("2 Corinthians",    "2Co", "New", "Pauline Epistles"),
    48: ("Galatians",        "Gal", "New", "Pauline Epistles"),
    49: ("Ephesians",        "Eph", "New", "Pauline Epistles"),
    50: ("Philippians",      "Phi", "New", "Pauline Epistles"),
    51: ("Colossians",       "Col", "New", "Pauline Epistles"),
    52: ("1 Thessalonians",  "1Th", "New", "Pauline Epistles"),
    53: ("2 Thessalonians",  "2Th", "New", "Pauline Epistles"),
    54: ("1 Timothy",        "1Ti", "New", "Pauline Epistles"),
    55: ("2 Timothy",        "2Ti", "New", "Pauline Epistles"),
    56: ("Titus",            "Tit", "New", "Pauline Epistles"),
    57: ("Philemon",         "Phm", "New", "Pauline Epistles"),
    58: ("Hebrews",          "Heb", "New", "General Epistles"),
    59: ("James",            "Jam", "New", "General Epistles"),
    60: ("1 Peter",          "1Pe", "New", "General Epistles"),
    61: ("2 Peter",          "2Pe", "New", "General Epistles"),
    62: ("1 John",           "1Jo", "New", "General Epistles"),
    63: ("2 John",           "2Jo", "New", "General Epistles"),
    64: ("3 John",           "3Jo", "New", "General Epistles"),
    65: ("Jude",             "Jud", "New", "General Epistles"),
    66: ("Revelation",       "Rev", "New", "Prophecy"),
}

# ─── Text helpers ─────────────────────────────────────────────────────────────

# Matches TVM grammar codes: {(H8804)} or {(G5656)}
_TVM_INLINE_RE = re.compile(r'\{(\([HG]\d+\))\}')

# Matches a real strongs tag (not TVM): {H430} or {G3056}
_STRONGS_TAG_RE = re.compile(r'\{[HG]\d+\}')

# Matches: optional_word{STRONGS} optionally followed by {(TVM)}
# Captures: group(1)=word, group(2)=strongs_id, group(3)=tvm_code (or None)
_WORD_STRONGS_RE = re.compile(
    r'([a-zA-Z]*)\{([HG]\d+)\}(?:\{(\([HG]\d+\))\})?'
)


def clean_text(raw: str) -> str:
    """Strip all strongs and TVM tags, returning plain KJV text."""
    text = _TVM_INLINE_RE.sub('', raw)
    text = _STRONGS_TAG_RE.sub('', text)
    return ' '.join(text.split())


def parse_word_links(raw: str) -> list[tuple]:
    """
    Returns list of (word, strongs_id, tvm_code) tuples in verse word order.

    - word       : the KJV English word; None for untranslated Hebrew particles
    - strongs_id : e.g. 'H430', 'G3056'
    - tvm_code   : per-word grammar code e.g. 'H8804' (stripped of parens);
                   None if the word has no grammar annotation
    """
    results = []
    for m in _WORD_STRONGS_RE.finditer(raw):
        word      = m.group(1) or None
        strongs   = m.group(2)
        tvm_raw   = m.group(3)
        # tvm_raw is like "(H8804)" — strip the parens to store just "H8804"
        tvm_code  = tvm_raw[1:-1] if tvm_raw else None
        results.append((word, strongs, tvm_code))
    return results


# ─── Seeding functions ────────────────────────────────────────────────────────

def seed_books(cur) -> dict[int, int]:
    """Insert 66 books. Returns {book_number: db_id}."""
    print("  Seeding books ...")
    rows = [
        (book_num, name, abbr, testament, category)
        for book_num, (name, abbr, testament, category) in BOOK_METADATA.items()
    ]
    execute_values(cur, """
        INSERT INTO book (book_number, name, abbreviation, testament, category)
        VALUES %s
        ON CONFLICT (book_number) DO UPDATE SET
            name         = EXCLUDED.name,
            abbreviation = EXCLUDED.abbreviation,
            testament    = EXCLUDED.testament,
            category     = EXCLUDED.category
        RETURNING book_number, id
    """, rows)
    book_map = {row[0]: row[1] for row in cur.fetchall()}
    print(f"    {len(book_map)} books seeded.")
    return book_map


def seed_chapters(cur, verses_data: list, book_map: dict) -> dict[tuple, int]:
    """
    Derive unique (book_number, chapter_number) pairs and insert.
    Returns {(book_db_id, chapter_number): chapter_db_id}.
    """
    print("  Seeding chapters ...")
    unique_chapters = sorted(set(
        (v['book'], v['chapter']) for v in verses_data
    ))
    rows = [
        (chapter_num, book_map[book_num])
        for book_num, chapter_num in unique_chapters
    ]
    execute_values(cur, """
        INSERT INTO chapter (chapter_number, book_id)
        VALUES %s
        ON CONFLICT DO NOTHING
    """, rows)
    # Re-query because ON CONFLICT DO NOTHING doesn't return skipped rows
    cur.execute("SELECT chapter_number, book_id, id FROM chapter")
    chapter_map = {(row[1], row[0]): row[2] for row in cur.fetchall()}
    print(f"    {len(chapter_map)} chapters seeded.")
    return chapter_map


def seed_verses_and_links(cur, verses_data: list, book_map: dict, chapter_map: dict):
    """
    Two-pass approach:
      Pass 1 — insert all verses, then re-query to build a reliable id map.
      Pass 2 — insert all VerseWordLinks using that map.
    """
    print("  Seeding verses ...")
    total_verses = len(verses_data)

    verse_rows = []
    for v in verses_data:
        book_db_id   = book_map[v['book']]
        chapter_db_id = chapter_map[(book_db_id, v['chapter'])]
        verse_rows.append((v['verse'], chapter_db_id, clean_text(v['text'])))

    for start in range(0, total_verses, BATCH_SIZE):
        batch = verse_rows[start: start + BATCH_SIZE]
        execute_values(cur, """
            INSERT INTO verse (verse_number, chapter_id, text)
            VALUES %s
            ON CONFLICT DO NOTHING
        """, batch)
        pct = min(start + BATCH_SIZE, total_verses) / total_verses * 100
        print(f"    verses  {min(start + BATCH_SIZE, total_verses):>6,} / {total_verses:,}  ({pct:.1f}%)", end="\r")

    print()

    # Reliable verse map: (chapter_id, verse_number) -> verse_id
    cur.execute("SELECT id, chapter_id, verse_number FROM verse")
    verse_map = {(row[1], row[2]): row[0] for row in cur.fetchall()}
    print(f"    {len(verse_map):,} verses confirmed in database.")

    print("  Seeding verse word links ...")
    link_rows = []
    for v in verses_data:
        book_db_id    = book_map[v['book']]
        chapter_db_id = chapter_map[(book_db_id, v['chapter'])]
        verse_db_id   = verse_map[(chapter_db_id, v['verse'])]

        for idx, (word, strongs_id, tvm_code) in enumerate(parse_word_links(v['text'])):
            link_rows.append((
                verse_db_id,
                strongs_id,
                idx,        # word_in_text_index (0-based)
                word,       # None for untranslated Hebrew particles
                tvm_code,   # None if word has no grammar annotation
            ))

    total_links   = len(link_rows)
    inserted_links = 0
    for start in range(0, total_links, BATCH_SIZE):
        batch = link_rows[start: start + BATCH_SIZE]
        execute_values(cur, """
            INSERT INTO versewordlink
                (verse_id, lex_id, word_in_text_index, word_in_text, tvm_code)
            VALUES %s
            ON CONFLICT DO NOTHING
        """, batch)
        inserted_links += len(batch)
        pct = inserted_links / total_links * 100
        print(f"    links  {inserted_links:>7,} / {total_links:,}  ({pct:.1f}%)", end="\r")

    print(f"\n    {inserted_links:,} verse word links seeded.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def seed():
    print(f"Loading {JSON_FILE} ...")
    with open(JSON_FILE, encoding="utf-8") as f:
        data = json.load(f)
    verses_data = data["verses"]
    print(f"    {len(verses_data):,} verses found.")

    print("Connecting to database ...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
    except Exception as e:
        sys.exit(f"Connection failed: {e}")

    conn.autocommit = False
    cur = conn.cursor()

    try:
        book_map    = seed_books(cur)
        chapter_map = seed_chapters(cur, verses_data, book_map)
        seed_verses_and_links(cur, verses_data, book_map, chapter_map)
        conn.commit()
        print("\nAll done -- Bible data seeded successfully.")

    except Exception as e:
        conn.rollback()
        sys.exit(f"\nSeeding failed (rolled back): {e}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    seed()
