"""
seed_lexicon.py
---------------
Seeds Strong's definitions from strongs_definitions.json into the `lexicon` table.

Column names match the Lexicon SQLModel in models.py exactly:
    strongs_id        TEXT  PRIMARY KEY  e.g. "H1", "G3056"
    language          TEXT               "H" (Hebrew) or "G" (Greek)
    hebrew_greek_word TEXT               original script, HTML-entity-decoded
    transliteration   TEXT
    pronunciation     TEXT
    tvm               TEXT               Tense/Voice/Mood (Hebrew only, usually NULL)
    definition        TEXT               cleaned HTML -> plain text

Usage:
    1. Set DATABASE_URL in a .env file or as an environment variable.
    2. pip install psycopg2-binary python-dotenv
    3. python seed_lexicon.py
"""

import json
import os
import re
import sys
from html import unescape
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
    pass  # python-dotenv not installed; rely on real env vars

# ─── Configuration ────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

JSON_FILE = Path(__file__).parent / "strongs_definitions.json"

TABLE_NAME = "lexicon"

# Column order must match the tuple returned by transform() below.
# These names match the Lexicon SQLModel fields in models.py exactly.
COLUMNS = [
    "strongs_id",         # JSON: number       (PK)
    "language",           # derived from number[0]
    "hebrew_greek_word",  # JSON: root_word
    "transliteration",    # JSON: transliteration
    "pronunciation",      # JSON: pronunciation
    "tvm",                # JSON: tvm
    "definition",         # JSON: entry
]

PK_COLUMN = "strongs_id"

BATCH_SIZE = 500  # rows per INSERT batch

# ─── Helpers ──────────────────────────────────────────────────────────────────

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")
_MULTI_NL_RE = re.compile(r"\n{3,}")


def clean_html(text: str | None) -> str | None:
    """Decode HTML entities and strip all tags, returning clean plain text."""
    if text is None:
        return None
    text = unescape(text)               # &#1488; -> alef, &amp; -> &
    text = _HTML_TAG_RE.sub(" ", text)  # strip <i>, <b>, <br> etc.
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _MULTI_NL_RE.sub("\n\n", text)
    return text.strip() or None


def decode_word(text: str | None) -> str | None:
    """Decode HTML entities only -- preserves Hebrew/Greek Unicode script."""
    if text is None:
        return None
    return unescape(text).strip() or None


def transform(record: dict) -> tuple:
    """Convert one JSON record into a DB row tuple ordered by COLUMNS."""
    number: str = record["number"]   # e.g. "H1" or "G3056"
    language: str = number[0]        # "H" or "G"

    return (
        number,                                      # strongs_id
        language,                                    # language
        decode_word(record.get("root_word")),        # hebrew_greek_word
        decode_word(record.get("transliteration")),  # transliteration
        record.get("pronunciation"),                 # pronunciation (plain ASCII)
        clean_html(record.get("tvm")),               # tvm
        clean_html(record.get("entry")),             # definition
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def seed():
    print(f"Loading {JSON_FILE} ...")
    with open(JSON_FILE, encoding="utf-8") as f:
        raw: list[dict] = json.load(f)
    print(f"    {len(raw):,} records found.")

    rows = [transform(r) for r in raw]

    col_list = ", ".join(COLUMNS)
    update_clause = ", ".join(
        f"{c} = EXCLUDED.{c}" for c in COLUMNS if c != PK_COLUMN
    )

    sql = f"""
        INSERT INTO {TABLE_NAME} ({col_list})
        VALUES %s
        ON CONFLICT ({PK_COLUMN}) DO UPDATE SET {update_clause}
    """

    print("Connecting to database ...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
    except Exception as e:
        sys.exit(f"Connection failed: {e}")

    conn.autocommit = False
    cur = conn.cursor()

    total = len(rows)
    inserted = 0

    try:
        for start in range(0, total, BATCH_SIZE):
            batch = rows[start : start + BATCH_SIZE]
            execute_values(cur, sql, batch)
            inserted += len(batch)
            pct = inserted / total * 100
            print(f"    {inserted:>6,} / {total:,}  ({pct:.1f}%)", end="\r")

        conn.commit()
        print(f"\nDone -- {inserted:,} rows upserted into `{TABLE_NAME}`.")

    except Exception as e:
        conn.rollback()
        sys.exit(f"\nSeeding failed (rolled back): {e}")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    seed()
