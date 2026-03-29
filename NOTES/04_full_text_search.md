# 04 — Full-Text Search

PostgreSQL has a built-in full-text search engine that is far faster and smarter
than a simple `ILIKE '%word%'` query. It handles stemming (so "run" matches
"running" and "ran"), ranking by relevance, and multi-word phrase queries.

This is the right tool for a Bible search feature like "search all verses".

---

## How it works

PostgreSQL converts text into a `tsvector` — a sorted list of normalised word stems.
A search query is converted into a `tsquery`. PostgreSQL then matches them and can
rank results by how well they match.

---

## Setup: add the search_vector column

This is done directly in PostgreSQL, not through SQLModel. Run this after seeding:

```sql
-- Add the column (stores the pre-computed search index)
ALTER TABLE verse ADD COLUMN search_vector tsvector;

-- Populate it for all existing rows
UPDATE verse SET search_vector = to_tsvector('english', text);

-- Create a GIN index for fast searching
CREATE INDEX idx_verse_search ON verse USING GIN(search_vector);

-- Create a trigger so new rows auto-populate the column
CREATE TRIGGER verse_search_vector_update
BEFORE INSERT OR UPDATE ON verse
FOR EACH ROW EXECUTE FUNCTION
    tsvector_update_trigger(search_vector, 'pg_catalog.english', text);
```

---

## Searching

```sql
-- Basic search: find verses containing "living water"
SELECT vf.book_name, vf.chapter_number, vf.verse_number, vf.text
FROM verse v
JOIN verse_full vf ON vf.verse_id = v.id
WHERE v.search_vector @@ to_tsquery('english', 'living & water')
ORDER BY ts_rank(v.search_vector, to_tsquery('english', 'living & water')) DESC;
```

```sql
-- Phrase search: words must appear adjacent (PostgreSQL 9.6+)
WHERE v.search_vector @@ phraseto_tsquery('english', 'fear not')
```

```sql
-- OR search: verses containing either "grace" or "mercy"
WHERE v.search_vector @@ to_tsquery('english', 'grace | mercy')
```

---

## FastAPI implementation

```python
from sqlmodel import text

@app.get("/search")
def search_verses(q: str, testament: str = None, session: Session = Depends(get_session)):
    query = """
        SELECT vf.book_name, vf.chapter_number, vf.verse_number, v.text,
               ts_rank(v.search_vector, query) AS rank
        FROM verse v
        JOIN verse_full vf ON vf.verse_id = v.id,
             to_tsquery('english', :q) query
        WHERE v.search_vector @@ query
    """
    params = {"q": " & ".join(q.split())}  # "living water" -> "living & water"

    if testament:
        query += " AND vf.testament = :testament"
        params["testament"] = testament

    query += " ORDER BY rank DESC LIMIT 50"
    results = session.exec(text(query).bindparams(**params)).all()
    return results
```

---

## Why not just use ILIKE?

`ILIKE '%word%'` scans every row in the table every time. On 31,102 verses this
is fast enough for development, but under real usage with multiple concurrent
users it will become a bottleneck. The GIN index approach above pre-computes the
search data so queries are near-instant regardless of load.
