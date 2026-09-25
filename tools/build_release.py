#!/usr/bin/env python3
"""Build and validate reproducible SQLite release assets. Python 3.11+, no dependencies."""
import csv
import hashlib
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import tomllib
import uuid

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_name(value):
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]*', value):
        raise ValueError(f'Invalid identifier: {value!r}')
    return value


def validate_database(db):
    if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise ValueError('SQLite integrity check failed')
    if db.execute('PRAGMA foreign_key_check').fetchall():
        raise ValueError('SQLite foreign key check failed')


def build():
    config = tomllib.loads((ROOT / 'content/catalog.toml').read_text())
    catalog_info = config['catalog']
    repository = catalog_info['repository']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Invalid GitHub repository')
    tag = valid_name(catalog_info['release_tag'])
    for key in ['version', 'schema_version', 'min_reader_version']:
        if type(catalog_info[key]) is not int or catalog_info[key] < 1:
            raise ValueError(f'Invalid catalog {key}')
    if catalog_info['schema_version'] != 1:
        raise ValueError('This builder supports schema 1 only')
    if not config['books']:
        raise ValueError('Catalog must contain at least one book')
    destination = ROOT / 'dist' / tag
    with tempfile.TemporaryDirectory() as temporary:
        staging = Path(temporary)
        catalog = sqlite3.connect(staging / 'catalog.sqlite')
        catalog.executescript('''PRAGMA user_version=1;
        CREATE TABLE catalog_metadata (
          singleton INTEGER PRIMARY KEY CHECK(singleton=1), catalog_version INTEGER NOT NULL,
          schema_version INTEGER NOT NULL, min_reader_version INTEGER NOT NULL,
          repository TEXT NOT NULL, release_tag TEXT NOT NULL);
        CREATE TABLE books (
          book_id TEXT PRIMARY KEY, title_en TEXT NOT NULL, title_bn TEXT NOT NULL,
          content_version INTEGER NOT NULL, schema_version INTEGER NOT NULL,
          entry_count INTEGER NOT NULL, file_name TEXT NOT NULL,
          byte_size INTEGER NOT NULL, sha256 TEXT NOT NULL,
          download_url TEXT NOT NULL, min_reader_version INTEGER NOT NULL);
        ''')
        catalog.execute('INSERT INTO catalog_metadata VALUES (1,?,?,?,?,?)', (
            catalog_info['version'], 1, catalog_info['min_reader_version'], repository, tag))
        for book in config['books']:
            ident = valid_name(book['id'])
            version = book['version']
            release_tag = valid_name(book['release_tag'])
            if type(version) is not int or version < 1 or book['schema_version'] != 1:
                raise ValueError(f'{ident}: invalid version or unsupported schema')
            with (ROOT / 'content/books' / f'{ident}.tsv').open(encoding='utf-8', newline='') as source:
                rows = list(csv.DictReader(source, delimiter='\t'))
            if len(rows) != book['entry_count'] or not rows:
                raise ValueError(f'{ident}: review the entry count')
            file_name = f'{ident}-v{version}.sqlite'
            path = staging / file_name
            db = sqlite3.connect(path)
            db.execute('PRAGMA foreign_keys=ON')
            db.executescript((ROOT / 'content/book-schema.sql').read_text())
            db.execute('INSERT INTO books VALUES (?,?,?,?,?,?,?)', (
                ident, book['title_en'], book['title_bn'], version, 1, len(rows), book['source_notice']))
            seen_order = set()
            for row in rows:
                # Validation never creates or rewrites editorial identity.
                for key in ['entry_id', 'meaning_id']:
                    if str(uuid.UUID(row[key])) != row[key]:
                        raise ValueError(f'{ident}: noncanonical stable UUID')
                order = int(row['sort_order'])
                if order in seen_order:
                    raise ValueError(f'{ident}: duplicate sort order')
                seen_order.add(order)
                db.execute('INSERT INTO entries VALUES (?,?,?,?,?,?)', (
                    row['entry_id'], ident, row['arabic'], order,
                    row['source_volume'] or None, row['source_chapter'] or None))
                db.execute('INSERT INTO meanings VALUES (?,?,?,?)', (
                    row['meaning_id'], row['entry_id'], book['language'], row['meaning']))
            db.commit()
            validate_database(db)
            db.close()
            digest = sha256(path)
            if digest != book['sha256']:
                raise ValueError(f'{ident}: content hash changed ({digest}); review version and expected hash before publishing')
            url = f'https://github.com/{repository}/releases/download/{release_tag}/{file_name}'
            catalog.execute('INSERT INTO books VALUES (?,?,?,?,?,?,?,?,?,?,?)', (
                ident, book['title_en'], book['title_bn'], version, 1, len(rows),
                file_name, path.stat().st_size, digest, url, book['min_reader_version']))
        catalog.commit()
        validate_database(catalog)
        catalog.close()
        shutil.copyfile(ROOT / 'RELEASE.md', staging / 'RELEASE.md')
        shutil.copyfile(ROOT / 'content/books/README.md', staging / 'SOURCES.md')
        files = sorted(staging.iterdir())
        (staging / 'SHA256SUMS').write_text(''.join(f'{sha256(f)}  {f.name}\n' for f in files))
        # Dist is generated, ignored output. A failed build never updates the prior output.
        destination.parent.mkdir(exist_ok=True)
        if destination.exists():
            existing = {p.name: p.read_bytes() for p in destination.iterdir()}
            generated = {p.name: p.read_bytes() for p in staging.iterdir()}
            if existing != generated:
                raise ValueError('Release output already exists with different bytes; use a new release tag')
        else:
            shutil.copytree(staging, destination)
    print(f'Ready: {destination} ({len(config["books"])} books, {sum(b["entry_count"] for b in config["books"])} entries)')
    return destination, config


if __name__ == '__main__':
    build()
