# Vocabulary source provenance

These TSV files are the editorial sources for the new SQLite books. Release consumers read SQLite files, not these TSV files.
Run `python3 tools/build_release.py` from this repository to build release assets.
The source paths below refer to the original app repository:
https://github.com/Abid-Hasan/my_arabic_vocab

- `125-words`: all 125 records from `assets/json/125_words.json`, English meanings.
- `esho-arbi-shikhi`: 819 usable records from 820 source records in
  `assets/json/esho_arbi_shikhi.json`, Bengali meanings. Original volume/chapter
  metadata, spelling and meanings are preserved without normalization.
- Quarantined source row **488** (one-based): Arabic text is missing; meaning
  `অভিমুখী হওয়া`, volume 2, chapter 1, original timeModified
  `2013-02-28T00:00:00.000`. It remains in the original JSON and is not invented
  or silently counted as usable vocabulary. An editor must supply the source word.
- The remote-only Haiyya book is unavailable until an authorized export is provided.

UUIDs were assigned once and persisted here. They are not row numbers, text hashes
or normalized Arabic. Preserve entry_id and meaning_id when editing text or order;
never recycle removed IDs. source_row is provenance, not identity. Same spelling
and different meanings remain separate entries. The original JSON is retained for
legacy compatibility and provenance; only the separate legacy entry point uses it.

Version 1 preserves the app's bundled development snapshot byte for byte and is
prepared for an initial remote release. The original source does not establish a new
license here; preserve applicable upstream attribution and rights. The quarantined
record remains excluded pending an editorial correction. Once published, use new
versions and filenames for changed content and retain previous release assets.
