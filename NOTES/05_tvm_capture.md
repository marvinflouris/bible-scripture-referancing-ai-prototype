# 05 — TVM (Tense, Voice, Mood) Capture

## What TVM codes are

In the KJV + Strong's JSON, Hebrew verbs have grammar codes embedded inline that
look like this:

```
was{H1961}{(H8804)}
moved{H7363}{(H8764)}
created{H1254}{(H8804)}
```

The code in parentheses — `(H8804)`, `(H8764)` — is the TVM code. It describes
the grammatical form of that specific verb in that specific verse:
tense (perfect, imperfect, etc.), voice (Qal, Niphal, Piel, etc.), and mood
(indicative, imperative, etc.).

These are NOT lexicon entries — they do not point to a word in the Lexicon table.
They are grammatical metadata about how the word is used in this verse.

The current seed_bible.py strips them out and discards them. This file explains
how to capture them instead.

---

## Why this is valuable

With TVM codes captured, you can filter verses by grammar. For example:

- "Show me every verse where H559 (amar/said) appears in the imperative mood"
- "How many times does God speak using the perfect tense in Genesis?"
- "Find every use of the Niphal (passive) voice of H1254 (bara/created)"

This is the kind of grammatical analysis that seminary students and scholars
use Logos Bible Software ($300–$1,500) to perform. You can expose it for free.

---

## The TVM code lookup table

The code H8804 means "Qal Stem, Perfect Tense, Active Voice". The full meaning
of each code is explained in the `tvm` field of certain special Lexicon rows.
For example, Lexicon row H8804 contains the explanation of that grammar pattern.

This means your Lexicon table already holds the TVM definitions — they were
seeded along with the word definitions. You just need to capture the per-word
codes in VerseWordLink.

---

## How to update the seeder to capture TVM codes

In `seed_bible.py`, the `parse_word_links` function currently does this:

```python
# Current: strips TVM codes entirely
text = _TVM_RE.sub('', raw)
```

Replace the function with this version that captures the TVM code alongside each word:

```python
def parse_word_links(raw: str) -> list[tuple]:
    """
    Returns list of (word, strongs_id, tvm_code) tuples.
    tvm_code is the grammar code for the word, or None if not present.
    """
    results = []
    # Find: word{STRONGS} optionally followed by {(TVM)}
    pattern = re.compile(r'([a-zA-Z]*)\{([HG]\d+)\}(?:\{\(([HG]\d+)\)\})?')
    for m in pattern.finditer(raw):
        word = m.group(1) if m.group(1) else None
        strongs_id = m.group(2)
        tvm_code = m.group(3)  # None if not present
        results.append((word, strongs_id, tvm_code))
    return results
```

Then update the link_rows tuple in `seed_verses_and_links` to include tvm_code:

```python
for idx, (word, strongs_id, tvm_code) in enumerate(word_links):
    link_rows.append((
        verse_db_id,
        strongs_id,
        idx,
        word,
        tvm_code,   # add this
    ))
```

And update the INSERT statement to include the column:

```sql
INSERT INTO versewordlink (verse_id, lex_id, word_in_text_index, word_in_text, tvm_code)
VALUES %s
```

---

## Querying with TVM

Once captured, you can join VerseWordLink to Lexicon twice — once for the word
definition, once for the grammar definition:

```sql
SELECT
    vwl.word_in_text,
    word_lex.definition       AS word_definition,
    tvm_lex.definition        AS grammar_description
FROM versewordlink vwl
JOIN lexicon word_lex ON word_lex.strongs_id = vwl.lex_id
LEFT JOIN lexicon tvm_lex ON tvm_lex.strongs_id = vwl.tvm_code
WHERE vwl.lex_id = 'H1254'   -- bara (created)
LIMIT 20;
```
