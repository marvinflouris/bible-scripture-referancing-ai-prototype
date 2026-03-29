# 07 — Book Abbreviations

Standard abbreviations for all 66 books. These should be seeded into the
`abbreviation` column of the Book table. They are used in API URL slugs,
verse references, and UI display.

Update `BOOK_METADATA` in `seed_bible.py` to add the abbreviation as a fourth
value in each tuple, then add it to the INSERT statement.

---

## Old Testament

| # | Name | Abbreviation |
|---|---|---|
| 1 | Genesis | Gen |
| 2 | Exodus | Exo |
| 3 | Leviticus | Lev |
| 4 | Numbers | Num |
| 5 | Deuteronomy | Deu |
| 6 | Joshua | Jos |
| 7 | Judges | Jdg |
| 8 | Ruth | Rut |
| 9 | 1 Samuel | 1Sa |
| 10 | 2 Samuel | 2Sa |
| 11 | 1 Kings | 1Ki |
| 12 | 2 Kings | 2Ki |
| 13 | 1 Chronicles | 1Ch |
| 14 | 2 Chronicles | 2Ch |
| 15 | Ezra | Ezr |
| 16 | Nehemiah | Neh |
| 17 | Esther | Est |
| 18 | Job | Job |
| 19 | Psalms | Psa |
| 20 | Proverbs | Pro |
| 21 | Ecclesiastes | Ecc |
| 22 | Song of Solomon | Sol |
| 23 | Isaiah | Isa |
| 24 | Jeremiah | Jer |
| 25 | Lamentations | Lam |
| 26 | Ezekiel | Eze |
| 27 | Daniel | Dan |
| 28 | Hosea | Hos |
| 29 | Joel | Joe |
| 30 | Amos | Amo |
| 31 | Obadiah | Oba |
| 32 | Jonah | Jon |
| 33 | Micah | Mic |
| 34 | Nahum | Nah |
| 35 | Habakkuk | Hab |
| 36 | Zephaniah | Zep |
| 37 | Haggai | Hag |
| 38 | Zechariah | Zec |
| 39 | Malachi | Mal |

## New Testament

| # | Name | Abbreviation |
|---|---|---|
| 40 | Matthew | Mat |
| 41 | Mark | Mar |
| 42 | Luke | Luk |
| 43 | John | Joh |
| 44 | Acts | Act |
| 45 | Romans | Rom |
| 46 | 1 Corinthians | 1Co |
| 47 | 2 Corinthians | 2Co |
| 48 | Galatians | Gal |
| 49 | Ephesians | Eph |
| 50 | Philippians | Phi |
| 51 | Colossians | Col |
| 52 | 1 Thessalonians | 1Th |
| 53 | 2 Thessalonians | 2Th |
| 54 | 1 Timothy | 1Ti |
| 55 | 2 Timothy | 2Ti |
| 56 | Titus | Tit |
| 57 | Philemon | Phm |
| 58 | Hebrews | Heb |
| 59 | James | Jam |
| 60 | 1 Peter | 1Pe |
| 61 | 2 Peter | 2Pe |
| 62 | 1 John | 1Jo |
| 63 | 2 John | 2Jo |
| 64 | 3 John | 3Jo |
| 65 | Jude | Jud |
| 66 | Revelation | Rev |

---

## Usage in API routes

Abbreviations let you write clean URL slugs:

```
GET /verse/Gen/1/1         instead of  GET /verse/Genesis/1/1
GET /verse/1Jo/3/16        instead of  GET /verse/1%20John/3/16
```

Note that "1 John", "2 Kings" etc. have spaces — abbreviations avoid the need
for URL encoding. Always support both the full name and the abbreviation in your
route handler.

```python
@app.get("/verse/{book_ref}/{chapter}/{verse_num}")
def get_verse(book_ref: str, chapter: int, verse_num: int, session: Session):
    # Accept both full name and abbreviation
    book = session.exec(
        select(Book).where(
            (Book.name == book_ref) | (Book.abbreviation == book_ref)
        )
    ).first()
```
