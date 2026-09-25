
PRAGMA user_version = 1;
CREATE TABLE books (
 book_id TEXT PRIMARY KEY, title_en TEXT NOT NULL, title_bn TEXT NOT NULL,
 content_version INTEGER NOT NULL, schema_version INTEGER NOT NULL,
 entry_count INTEGER NOT NULL, source TEXT NOT NULL
);
CREATE TABLE entries (
 entry_id TEXT PRIMARY KEY, book_id TEXT NOT NULL REFERENCES books(book_id),
 arabic TEXT NOT NULL CHECK(length(trim(arabic)) > 0), sort_order INTEGER NOT NULL,
 source_volume INTEGER, source_chapter INTEGER
);
CREATE TABLE meanings (
 meaning_id TEXT PRIMARY KEY, entry_id TEXT NOT NULL REFERENCES entries(entry_id),
 language_code TEXT NOT NULL, text TEXT NOT NULL CHECK(length(trim(text)) > 0)
);
CREATE INDEX meanings_entry ON meanings(entry_id);
