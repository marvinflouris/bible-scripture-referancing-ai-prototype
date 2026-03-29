# 01 — Querying Guide

## The golden rule

Always identify a verse by its three-part canonical reference:
**book_number + chapter_number + verse_number**

Never use the internal database `id` in user-facing routes or logic. The `id` is
an implementation detail. "Genesis 1:1" is the universal language.

Example API route shape:
```
GET /verse/Genesis/1/1
GET /verse/Gen/1/1        # using abbreviation
GET /books/1/chapters/1/verses/1
```

---

## Basic verse lookup (3-table join)

```sql
SELECT v.text, v.verse_number, c.chapter_number, b.name
FROM verse v
JOIN chapter c ON c.id = v.chapter_id
JOIN book b    ON b.id = c.book_id
WHERE b.book_number = 1
  AND c.chapter_number = 1
  AND v.verse_number = 1;
```

Once you create the `verse_full` view (see 03_indexes_and_views.md), this simplifies to:

```sql
SELECT * FROM verse_full
WHERE book_name = 'Genesis'
  AND chapter_number = 1
  AND verse_number = 1;
```

---

## Find all verses containing a specific Strong's word

This answers: "show me every place H430 (Elohim/God) appears in the Bible."

```sql
SELECT vf.book_name, vf.chapter_number, vf.verse_number, vf.text
FROM versewordlink vwl
JOIN verse_full vf ON vf.verse_id = vwl.verse_id
WHERE vwl.lex_id = 'H430'
ORDER BY vf.book_name, vf.chapter_number, vf.verse_number;
```

---

## Get all words in a verse with their Strong's roots

This is the foundation of the interlinear view:

```sql
SELECT
    vwl.word_in_text_index,
    vwl.word_in_text,
    l.strongs_id,
    l.hebrew_greek_word,
    l.transliteration,
    l.pronunciation,
    l.definition
FROM versewordlink vwl
JOIN lexicon l ON l.strongs_id = vwl.lex_id
JOIN verse_full vf ON vf.verse_id = vwl.verse_id
WHERE vf.book_name = 'Genesis'
  AND vf.chapter_number = 1
  AND vf.verse_number = 1
ORDER BY vwl.word_in_text_index;
```

---

## Filter by testament or category

```sql
-- All NT verses
SELECT v.text FROM verse_full v WHERE testament = 'New';

-- All verses from the Gospels
SELECT v.text FROM verse_full v WHERE category = 'Gospels';

-- All OT poetry books
SELECT DISTINCT book_name FROM verse_full WHERE category = 'Poetry';
```

---

## Searching for a word in the English text

For a simple ILIKE search (slow on large tables, fine for small apps):

```sql
SELECT book_name, chapter_number, verse_number, text
FROM verse_full
WHERE text ILIKE '%living water%';
```

For fast search, use the full-text search setup in 04_full_text_search.md instead.
