# v3_database — KJV Bible + Strong's Concordance

A PostgreSQL database containing the complete King James Bible with every English
word linked to its original Hebrew or Greek root via Strong's numbering system.

---

## What this database is

Every one of the 31,102 verses in the KJV has its words indexed and linked to the
Lexicon table, which contains 14,696 Strong's definitions (8,854 Hebrew + 5,842 Greek).
This means you can query any word in any verse and find out exactly what Hebrew or
Greek word was originally written there, what it means, and how it is pronounced.

---

## Stack

- Python 3.11+
- PostgreSQL 14+
- SQLModel (built on SQLAlchemy + Pydantic)
- psycopg2-binary (for seeding scripts)
- FastAPI (planned API layer)

---

## Project structure

```
project/
    models.py               -- SQLModel table definitions
    database.py             -- engine setup and table initialisation
    main.py                 -- FastAPI app entry point
    seed_lexicon.py         -- seeds Lexicon table from strongs_definitions.json
    seed_bible.py           -- seeds Book, Chapter, Verse, VerseWordLink tables
    strongs_definitions.json
    kjv_strongs.json
    requirements.txt
    notes/
        01_querying_guide.md
        02_interlinear_api.md
        03_indexes_and_views.md
        04_full_text_search.md
        05_tvm_capture.md
        06_concordance_features.md
        07_book_abbreviations.md
```

---

## Database schema

### Book
| Column | Type | Notes |
|---|---|---|
| id | int PK | auto |
| book_number | int UNIQUE | 1–66, canonical order |
| name | varchar(100) | e.g. "Genesis", "Matthew" |
| abbreviation | varchar(10) | e.g. "Gen", "Matt" |
| testament | varchar(20) | "Old" or "New" |
| category | varchar(50) | e.g. "Law", "Gospels", "Pauline Epistles" |

### Chapter
| Column | Type | Notes |
|---|---|---|
| id | int PK | auto |
| chapter_number | int | chapter number within its book |
| book_id | int FK | → book.id |

### Verse
| Column | Type | Notes |
|---|---|---|
| id | int PK | auto |
| verse_number | int | verse number within its chapter |
| chapter_id | int FK | → chapter.id |
| text | text | clean KJV text, strongs tags stripped |

### Lexicon
| Column | Type | Notes |
|---|---|---|
| strongs_id | varchar PK | e.g. "H1", "G3056" |
| language | char(1) | "H" (Hebrew) or "G" (Greek) |
| hebrew_greek_word | text | original script |
| transliteration | text | romanised form |
| pronunciation | text | plain English guide e.g. "awb" |
| tvm | text | general Tense/Voice/Mood notes (OT only) |
| definition | text | full Strong's definition, HTML stripped |

### VerseWordLink
| Column | Type | Notes |
|---|---|---|
| id | int PK | auto |
| verse_id | int FK | → verse.id |
| lex_id | varchar FK | → lexicon.strongs_id |
| word_in_text_index | int | 0-based word position in the verse |
| word_in_text | text | KJV English word; NULL for untranslated particles |
| tvm_code | varchar | per-word grammar code e.g. "H8804" (optional, see notes/05) |

---

## Seeding order

The tables have foreign key dependencies. Always seed in this order:

```bash
# 1. Create all tables
python database.py

# 2. Seed the lexicon first (VerseWordLink has FK to Lexicon)
python seed_lexicon.py

# 3. Seed Bible content (Book -> Chapter -> Verse -> VerseWordLink)
python seed_bible.py
```

Expected row counts after seeding:
- book: 66
- chapter: 1,189
- verse: 31,102
- lexicon: 14,696
- versewordlink: ~351,804

---

## Environment

Create a `.env` file in the project root:

```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/v3_database
```

Both seed scripts read this automatically.

---

## Recommended SQL to run after seeding

See `notes/03_indexes_and_views.md` for the full SQL. In summary:

```sql
-- Speed up VerseWordLink lookups
CREATE INDEX idx_vwl_verse_id ON versewordlink(verse_id);
CREATE INDEX idx_vwl_lex_id   ON versewordlink(lex_id);

-- Flat view for clean API queries (avoids 3-table joins every time)
CREATE VIEW verse_full AS
SELECT
    v.id          AS verse_id,
    v.verse_number,
    v.text,
    c.chapter_number,
    b.id          AS book_id,
    b.name        AS book_name,
    b.abbreviation,
    b.testament,
    b.category
FROM verse v
JOIN chapter c ON c.id = v.chapter_id
JOIN book b    ON b.id = c.book_id;
```

---

## Key design decisions

**Always reference verses by book_number + chapter_number + verse_number**, never
by the internal database id alone. The canonical reference system (Genesis 1:1,
John 3:16) is how every Bible tool in the world identifies verses, and your API
routes should mirror that.

**Untranslated particles are stored with word_in_text = NULL.** Hebrew grammar
includes particles like the direct object marker (aleph-tav, H853) that have no
English equivalent in the KJV. They appear in the source as `{H853}` with no word
before the tag. These are stored with NULL rather than an empty string so you can
easily filter them out or include them depending on context.

**TVM codes in the KJV text are skipped by default.** The raw JSON contains verb
grammar markers like `{(H8804)}` embedded inline. These indicate the tense, voice,
and mood of a specific verb in a specific verse. The current seeder discards them.
To capture them, add a `tvm_code` column to VerseWordLink and update seed_bible.py.
See `notes/05_tvm_capture.md`.

**Book categories are manually assigned**, not sourced from the JSON. The KJV JSON
only provides book names and numbers. The testament and category values in seed_bible.py
follow standard Protestant canon divisions. Some traditions categorise books
differently — be aware of this if you surface these labels to users.

---

## Notes and ideas

See the `notes/` folder for detailed guidance on:

| File | Topic |
|---|---|
| 01_querying_guide.md | How to query verses, words, and roots correctly |
| 02_interlinear_api.md | Building an interlinear endpoint |
| 03_indexes_and_views.md | Essential SQL indexes and the verse_full view |
| 04_full_text_search.md | PostgreSQL full-text search on verse text |
| 05_tvm_capture.md | Capturing verb tense/voice/mood per word |
| 06_concordance_features.md | Word frequency and concordance queries |
| 07_book_abbreviations.md | Standard Bible book abbreviations reference |
