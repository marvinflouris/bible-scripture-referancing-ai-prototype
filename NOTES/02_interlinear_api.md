# 02 — Interlinear API

An interlinear Bible shows each English word aligned directly above or below its
original Hebrew or Greek word. This is your most distinctive feature — it is rare
in free Bible APIs and extremely valuable to serious Bible students.

Your schema already supports it perfectly. Every word in every verse is linked to
its Strong's root via VerseWordLink, with `word_in_text_index` preserving order.

---

## What the endpoint should return

Example request:
```
GET /verse/Genesis/1/1/interlinear
```

Example response:
```json
{
  "reference": "Genesis 1:1",
  "testament": "Old",
  "words": [
    {
      "index": 0,
      "english": "In the beginning",
      "strongs_id": "H7225",
      "original": "רֵאשִׁית",
      "transliteration": "re'shiyth",
      "pronunciation": "ray-sheeth'",
      "definition": "The first, in place, time, order or rank..."
    },
    {
      "index": 1,
      "english": "God",
      "strongs_id": "H430",
      "original": "אֱלֹהִים",
      "transliteration": "'elohiym",
      "pronunciation": "el-o-heem'",
      "definition": "gods in the ordinary sense; but specifically used of the supreme God..."
    },
    {
      "index": 2,
      "english": null,
      "strongs_id": "H853",
      "original": "אֵת",
      "transliteration": "'eth",
      "pronunciation": "ayth",
      "definition": "A particle indicating the direct object..."
    }
  ]
}
```

Note the third word has `english: null` — that is the untranslated direct object
marker (aleph-tav). Including it shows the user what the KJV left out, which is
genuinely useful for study.

---

## FastAPI implementation

```python
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select
from app.models import Book, Chapter, Verse, VerseWordLink, Lexicon

app = FastAPI()

@app.get("/verse/{book_name}/{chapter}/{verse_num}/interlinear")
def get_interlinear(book_name: str, chapter: int, verse_num: int, session: Session):

    # Resolve the verse id
    statement = (
        select(Verse, Chapter, Book)
        .join(Chapter, Chapter.id == Verse.chapter_id)
        .join(Book, Book.id == Chapter.book_id)
        .where(Book.name == book_name)
        .where(Chapter.chapter_number == chapter)
        .where(Verse.verse_number == verse_num)
    )
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Verse not found")

    verse, chap, book = result

    # Fetch all word links for this verse, ordered
    links = session.exec(
        select(VerseWordLink, Lexicon)
        .join(Lexicon, Lexicon.strongs_id == VerseWordLink.lex_id)
        .where(VerseWordLink.verse_id == verse.id)
        .order_by(VerseWordLink.word_in_text_index)
    ).all()

    words = [
        {
            "index": vwl.word_in_text_index,
            "english": vwl.word_in_text,
            "strongs_id": lex.strongs_id,
            "original": lex.hebrew_greek_word,
            "transliteration": lex.transliteration,
            "pronunciation": lex.pronunciation,
            "definition": lex.definition,
        }
        for vwl, lex in links
    ]

    return {
        "reference": f"{book.name} {chapter}:{verse_num}",
        "testament": book.testament,
        "plain_text": verse.text,
        "words": words,
    }
```

---

## Why this is rare and valuable

Most free Bible APIs (bible-api.com, api.bible) return only verse text. A few
return Strong's numbers alongside the text but not the full lexicon entry. Almost
none return the original script word, transliteration, pronunciation, AND definition
for every word in a single structured response. You can do all of that.

---

## Suggested additional interlinear endpoints

```
GET /word/{strongs_id}                  -- full lexicon entry for one word
GET /word/{strongs_id}/verses           -- all verses where this word appears
GET /verse/{book}/{chapter}/{verse}/words  -- same as interlinear but lighter (no definitions)
```
