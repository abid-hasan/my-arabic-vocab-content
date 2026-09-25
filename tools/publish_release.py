#!/usr/bin/env python3
"""Explicit release publication: build, stage draft assets, verify downloads, publish last."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from build_release import ROOT, build, sha256


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true', help='Create/upload/publish the configured release')
    parser.add_argument('--resume-draft', action='store_true', help='Resume only an existing draft on this same source commit')
    args = parser.parse_args()
    folder, config = build()
    catalog = config['catalog']
    repository, tag = catalog['repository'], catalog['release_tag']
    if not args.publish:
        print(f'Prepared {tag} for {repository}; no network writes. Use --publish after source is committed and pushed.')
        return
    if run('git', 'status', '--porcelain'):
        raise SystemExit('Source must be committed with a clean working tree before publication.')
    commit = run('git', 'rev-parse', 'HEAD')
    remote_commit = run('gh', 'api', f'repos/{repository}/commits/{commit}', '--jq', '.sha')
    if remote_commit != commit:
        raise SystemExit('Push this source commit before publishing.')
    # Also validate every unchanged book referenced by an older release.
    with tempfile.TemporaryDirectory() as temporary:
        for book in config['books']:
            if book['release_tag'] == tag:
                continue
            name = f'{book["id"]}-v{book["version"]}.sqlite'
            target = Path(temporary) / book['id']
            run('gh', 'release', 'download', book['release_tag'], '--repo', repository,
                '--pattern', name, '--dir', str(target))
            if sha256(target / name) != book['sha256']:
                raise SystemExit(f'Published book mismatch: {name}')
    # Draft releases may not resolve through the release-by-tag REST endpoint.
    releases = json.loads(run('gh', 'api', '--paginate', '--slurp',
        f'repos/{repository}/releases?per_page=100'))
    release = next((r for page in releases for r in page if r['tag_name'] == tag), None)
    if release is not None:
        if not args.resume_draft or not release['draft'] or release['target_commitish'] != commit:
            raise SystemExit('Release already exists. Only same-commit drafts can be resumed explicitly.')
    else:
        if args.resume_draft:
            raise SystemExit('No draft exists to resume.')
        run('gh', 'release', 'create', tag, '--repo', repository, '--draft', '--target', commit,
            '--title', f'Vocabulary content {catalog["version"]}', '--notes-file', str(ROOT / 'RELEASE.md'))
        releases = json.loads(run('gh', 'api', '--paginate', '--slurp',
            f'repos/{repository}/releases?per_page=100'))
        release = next(r for page in releases for r in page if r['tag_name'] == tag)
    existing_assets = {a['name'] for a in release['assets']}
    local_assets = {p.name for p in folder.iterdir()}
    if existing_assets - local_assets:
        raise SystemExit('Draft contains unexpected assets; inspect it before resuming.')
    for path in sorted(folder.iterdir()):
        if path.name not in existing_assets:
            run('gh', 'release', 'upload', tag, str(path), '--repo', repository)
    # An interrupted or wrong upload cannot become public via this tool.
    with tempfile.TemporaryDirectory() as temporary:
        run('gh', 'release', 'download', tag, '--repo', repository, '--dir', temporary)
        for path in folder.iterdir():
            if sha256(Path(temporary) / path.name) != sha256(path):
                raise SystemExit(f'Draft checksum mismatch: {path.name}; draft left unpublished.')
    run('gh', 'release', 'edit', tag, '--repo', repository, '--draft=false', '--latest')
    print(f'Published https://github.com/{repository}/releases/tag/{tag}')


if __name__ == '__main__':
    main()
