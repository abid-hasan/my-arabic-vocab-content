# Vocabulary content 1

Initial SQLite snapshot matching the app's bundled book databases:

- 125 Words: 125 entries with English meanings.
- Esho Arbi Shikhi: 819 entries with Bengali meanings.
- Catalog schema 1; minimum reader version 1.

Assets include `catalog.sqlite`, two versioned book databases, `SHA256SUMS`,
these release notes and `SOURCES.md`. Existing stable entry/meaning IDs are preserved.
The source row with missing Arabic and the unavailable remote-only Haiyya book are
excluded; see `SOURCES.md`. App installation continues to use its bundled snapshot;
this release does not itself enable client updates.
