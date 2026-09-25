# My Arabic Vocab content

Public SQLite book distribution for My Arabic Vocab. This repository holds editorial
sources and release tooling; user accounts, progress and private data do not belong here.

Current prepared content: **3 books, 1,146 entries** (125 English meanings and 1,021 Bengali meanings).
See [source notes](content/books/README.md) for provenance and exclusions.

## Build and publish

Requires Python 3.11+ (standard library only). Publication also requires authenticated
GitHub CLI and a clean, committed source tree pushed to this repository.

```sh
python3 tools/build_release.py
python3 tools/publish_release.py
# After reviewing, committing and pushing the source:
python3 tools/publish_release.py --publish
```

The first two commands only prepare local files in `dist/content-v2/`. Publication
creates a draft, uploads assets, downloads and verifies every asset, then publishes.
For an interrupted draft on the same source commit, use `--publish --resume-draft`.
Published releases are never overwritten by the tool.

## Delivery contract

After the initial release is published, the catalog endpoint is:

https://github.com/abid-hasan/my-arabic-vocab-content/releases/latest/download/catalog.sqlite

The endpoint is live; it serves content-v1 until content-v2 is published. The catalog contains metadata and one row per
book: stable book ID, localized titles, content/schema/minimum reader versions, entry
count, filename, size, SHA-256 and a version-specific release download URL.
Book files contain `books`, `entries` and `meanings`; see `content/book-schema.sql`.
The app receives SQLite files, not the editorial TSV/TOML files.

The app should remain usable with bundled databases without a network connection.
Optional updates must validate supported schemas, file size, checksum and database
integrity before activating content. Personal data belongs in a separate database.
Client download/activation is a separate implementation milestone, not supplied here.
Checksums detect corruption; they do not independently authenticate the publisher.
Use HTTPS and the configured owner/repository as the distribution trust boundary.

## Future content changes

Preserve existing entry and meaning UUIDs. Edit the TSV, increase the affected book
version and release tag in `content/catalog.toml`, review the builder-reported new hash,
and update its pinned hash and expected count. Increase the catalog version and release
tag for each publication, and update `RELEASE.md`. Retain old release assets so existing
catalogs keep working. Unchanged books may reference their original release tags.
Never reuse a published version for different bytes. GitHub release immutability is not
configured by these scripts; administrators must also preserve published assets.

No new license or ownership claim is made for the source vocabulary.
