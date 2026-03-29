# 03 — Indexes and Views

Run this SQL immediately after seeding. Without the indexes, queries on
versewordlink (351,804 rows) will do full table scans and become noticeably
slow as your API gets real usage.

These are raw SQL commands to run directly in PostgreSQL — not through SQLModel,
because SQLModel does not manage indexes or views.

---

## Indexes

```sql
-- Speeds up: "get all words in verse X"
-- Used constantly by the interlinear and verse endpoints
CREATE INDEX idx_vwl_verse_id ON versewordlink(verse_id);

-- Speeds up: "find all verses containing Strong's word X"
-- Used by concordance and word-search endpoints
CREATE INDEX idx_vwl_lex_id ON versewordlink(lex_id);

-- Speeds up: looking up a verse by its position (book + chapter + verse number)
-- Used by every verse lookup
CREATE INDEX idx_verse_number ON verse(verse_number);
CREATE INDEX idx_chapter_number ON chapter(chapter_number);
CREATE INDEX idx_book_number ON book(book_number);
```

---

## The verse_full view

Without this view, every verse lookup requires a 3-table join (verse + chapter + book).
This view flattens them so your API queries become simple single-table selects.

```sql
CREATE VIEW verse_full AS
SELECT
    v.id              AS verse_id,
    v.verse_number,
    v.text,
    c.id              AS chapter_id,
    c.chapter_number,
    b.id              AS book_id,
    b.book_number,
    b.name            AS book_name,
    b.abbreviation,
    b.testament,
    b.category
FROM verse v
JOIN chapter c ON c.id = v.chapter_id
JOIN book b    ON b.id = c.book_id;
```

After creating this view, a verse lookup becomes:

```sql
SELECT * FROM verse_full
WHERE book_name = 'John'
  AND chapter_number = 3
  AND verse_number = 16;
```

---

## Verify index usage

After creating indexes, you can confirm PostgreSQL is using them with EXPLAIN:

```sql
EXPLAIN ANALYZE
SELECT * FROM versewordlink WHERE lex_id = 'H430';
```

You should see "Index Scan" in the output. If you see "Seq Scan" the index is not
being used — check that the column name matches exactly.

---

## Optional: index on word_in_text

If you plan to search across all words in the database (e.g. "find all occurrences
of the English word 'grace'"), add this too:

```sql
CREATE INDEX idx_vwl_word ON versewordlink(word_in_text);
```

This is lower priority than the verse_id and lex_id indexes.
