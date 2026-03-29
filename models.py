from sqlmodel import Relationship, SQLModel, Field
from typing import Optional, List


class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_number: int = Field(unique=True)                          # 1-66, matches JSON "book" field
    name: str = Field(max_length=100)                              # e.g. "Genesis", "Matthew"
    abbreviation: Optional[str] = Field(default=None, max_length=10)  # e.g. "Gen", "Matt", "Rev"
    testament: Optional[str] = Field(default=None, max_length=20)  # "Old" or "New"
    category: Optional[str] = Field(default=None, max_length=50)   # e.g. "Law", "Gospels"
    chapters: List["Chapter"] = Relationship(back_populates="book")


class Chapter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chapter_number: int                                            # chapter number within its book
    book_id: int = Field(foreign_key="book.id")
    book: Book = Relationship(back_populates="chapters")
    verses: List["Verse"] = Relationship(back_populates="chapter")


class Verse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    verse_number: int                                              # verse number within its chapter
    chapter_id: int = Field(foreign_key="chapter.id")
    chapter: Chapter = Relationship(back_populates="verses")
    text: str                                                      # clean KJV text, all strongs tags stripped
    # NOTE: Add a `search_vector` tsvector column directly in PostgreSQL (not via SQLModel).
    # See notes/04_full_text_search.md for the SQL.
    verse_word_links: List["VerseWordLink"] = Relationship(back_populates="verse")


class Lexicon(SQLModel, table=True):
    strongs_id: str = Field(primary_key=True)                      # e.g. "H1", "G3056"
    language: Optional[str] = Field(default=None, max_length=1)    # "H" or "G"
    hebrew_greek_word: Optional[str] = None                        # original script, HTML-entity-decoded
    transliteration: Optional[str] = None                          # romanised pronunciation guide
    pronunciation: Optional[str] = None                            # plain English pronunciation e.g. "awb"
    tvm: Optional[str] = None                                      # Tense/Voice/Mood explanatory text (OT only)
    definition: Optional[str] = None                               # full Strong's definition, HTML stripped
    verse_word_links: List["VerseWordLink"] = Relationship(back_populates="lexicon")


class VerseWordLink(SQLModel, table=True):
    """
    The bridge between every English word in the KJV and its original
    Hebrew or Greek root in the Lexicon.

    word_in_text_index is 0-based and preserves exact word order within
    the verse, enabling interlinear display.

    word_in_text is None for untranslated Hebrew particles (e.g. aleph-tav / H853)
    that are grammatically present in the original but have no English
    equivalent in the KJV translation.

    NOTE: Add DB indexes on (verse_id) and (lex_id) directly in PostgreSQL.
    See notes/03_indexes_and_views.md for the SQL.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    verse_id: int = Field(foreign_key="verse.id")
    lex_id: str = Field(foreign_key="lexicon.strongs_id")
    word_in_text_index: int                                        
    word_in_text: Optional[str] = None                               
    verse: "Verse" = Relationship(back_populates="verse_word_links")
    lexicon: "Lexicon" = Relationship(back_populates="verse_word_links")


print("All design blueprints secure! And well established.")

""" 
NOTE:   
    0-based position in the verse
    tvm_code: Optional[str] = None                                 
    per-word grammar code e.g. "H8804"
    KJV word; None for untranslated particles

    tvm_code captures verb tense/voice/mood for this specific word in this verse.
    See notes/05_tvm_capture.md to learn how to seed and use it.
"""