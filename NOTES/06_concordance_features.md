# 06 — Concordance Features

A concordance is an alphabetical index of every word in the Bible with a list of
every verse it appears in. Your database is a concordance — you just need to
query it the right way.

These are some of the most powerful features you can expose through your API,
and they are nearly free given the schema you already have.

---

## Word frequency: how many times does a word appear?

```sql
-- How many times does H430 (Elohim/God) appear in the entire Bible?
SELECT COUNT(*) FROM versewordlink WHERE lex_id = 'H430';

-- Frequency by testament
SELECT b.testament, COUNT(*) AS occurrences
FROM versewordlink vwl
JOIN verse v    ON v.id = vwl.verse_id
JOIN chapter c  ON c.id = v.chapter_id
JOIN book b     ON b.id = c.book_id
WHERE vwl.lex_id = 'H430'
GROUP BY b.testament;

-- Frequency by book, sorted most to least
SELECT b.name, COUNT(*) AS occurrences
FROM versewordlink vwl
JOIN verse v    ON v.id = vwl.verse_id
JOIN chapter c  ON c.id = v.chapter_id
JOIN book b     ON b.id = c.book_id
WHERE vwl.lex_id = 'H430'
GROUP BY b.name
ORDER BY occurrences DESC;
```

---

## Compare two words across the Bible

```sql
-- H430 (Elohim) vs H3068 (YHWH) occurrences by book
SELECT
    b.name,
    SUM(CASE WHEN vwl.lex_id = 'H430'  THEN 1 ELSE 0 END) AS elohim,
    SUM(CASE WHEN vwl.lex_id = 'H3068' THEN 1 ELSE 0 END) AS yhwh
FROM versewordlink vwl
JOIN verse v   ON v.id = vwl.verse_id
JOIN chapter c ON c.id = v.chapter_id
JOIN book b    ON b.id = c.book_id
WHERE vwl.lex_id IN ('H430', 'H3068')
GROUP BY b.name, b.book_number
ORDER BY b.book_number;
```

---

## Top N most-used words in a book or testament

```sql
-- Top 10 most used Hebrew roots in Genesis
SELECT vwl.lex_id, l.transliteration, l.definition, COUNT(*) AS uses
FROM versewordlink vwl
JOIN lexicon l  ON l.strongs_id = vwl.lex_id
JOIN verse v    ON v.id = vwl.verse_id
JOIN chapter c  ON c.id = v.chapter_id
JOIN book b     ON b.id = c.book_id
WHERE b.name = 'Genesis'
GROUP BY vwl.lex_id, l.transliteration, l.definition
ORDER BY uses DESC
LIMIT 10;
```

---

## Words unique to a specific book

```sql
-- Strong's IDs that appear in John but nowhere else in the NT
SELECT vwl.lex_id
FROM versewordlink vwl
JOIN verse v   ON v.id = vwl.verse_id
JOIN chapter c ON c.id = v.chapter_id
JOIN book b    ON b.id = c.book_id
WHERE b.name = 'John'
  AND vwl.lex_id LIKE 'G%'
EXCEPT
SELECT vwl.lex_id
FROM versewordlink vwl
JOIN verse v   ON v.id = vwl.verse_id
JOIN chapter c ON c.id = v.chapter_id
JOIN book b    ON b.id = c.book_id
WHERE b.testament = 'New'
  AND b.name != 'John';
```

---

## API endpoint ideas

```
GET /word/{strongs_id}/frequency          -- total count
GET /word/{strongs_id}/frequency/by-book  -- breakdown per book
GET /word/{strongs_id}/verses             -- all verses it appears in
GET /book/{name}/top-words?limit=20       -- most common roots in a book
GET /compare?words=H430,H3068            -- side-by-side frequency comparison
```

---

## Why this is significant

A printed concordance like Strong's Exhaustive Concordance is a 1,800-page book.
Scholars spend careers studying word usage patterns across the Biblical corpus.
You can answer these questions with a single SQL query in milliseconds.
