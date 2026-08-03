#!/usr/bin/env python3
"""Consolidate ad-hoc asset copies onto the manifest's canonical masters.

Before assets/manifest.json existed, pages were built against images pulled
straight from the CDN at ?format=1500w under hand-written names. sync_assets.py
later mirrored the same images at full resolution under deterministic names, so
each of those early files now has a higher-resolution twin.

This script pairs them by perceptual hash (identical picture, different size),
repoints every page at the canonical file, and deletes the superseded copy.
It reports anything it cannot pair rather than guessing.

    python3 tools/dedupe_assets.py --dry-run   # show the plan, change nothing
    python3 tools/dedupe_assets.py             # apply
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
MANIFEST = os.path.join(ASSETS, 'manifest.json')
HASH_SIZE = 16
# Max fraction of differing bits for two images to count as the same picture.
THRESHOLD = 0.10


def phash(path):
    """Average-hash: 16x16 greyscale, one bit per pixel vs. the mean."""
    try:
        with Image.open(path) as im:
            im = im.convert('L').resize((HASH_SIZE, HASH_SIZE), Image.LANCZOS)
            px = list(im.getdata())
    except Exception:
        return None
    avg = sum(px) / len(px)
    return [p > avg for p in px]


def distance(a, b):
    return sum(x != y for x, y in zip(a, b)) / len(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    manifest = json.load(open(MANIFEST))
    canonical = {m['local'] for m in manifest.values()}

    on_disk = []
    for dirpath, _, files in os.walk(ASSETS):
        for fn in files:
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT)
            if fn.endswith(('.json', '.pdf', '.svg')):
                continue
            # assets/brand/ is hand-curated: the logo and favicon deliberately
            # exist as both a WebP master and a PNG derivative (PNG because
            # favicons and some clients still need it). They look identical to
            # a perceptual hash, so leave the whole folder alone.
            if rel.startswith(os.path.join('assets', 'brand') + os.sep):
                continue
            on_disk.append(rel)

    legacy = sorted(p for p in on_disk if p not in canonical)
    masters = sorted(p for p in on_disk if p in canonical)
    print(f'{len(masters)} canonical masters, {len(legacy)} legacy files to resolve\n')

    print('Hashing…')
    mh = {p: phash(os.path.join(ROOT, p)) for p in masters}
    mh = {p: h for p, h in mh.items() if h}

    pairs, orphans = {}, []
    for lp in legacy:
        h = phash(os.path.join(ROOT, lp))
        if not h:
            orphans.append((lp, 'unreadable'))
            continue
        best, best_d = None, 1.0
        for mp, mhash in mh.items():
            d = distance(h, mhash)
            if d < best_d:
                best, best_d = mp, d
        if best and best_d <= THRESHOLD:
            pairs[lp] = (best, best_d)
        else:
            orphans.append((lp, f'no match (closest {best_d:.2f})'))

    print(f'\n{len(pairs)} legacy files matched to a master, {len(orphans)} unmatched\n')

    # Which pages reference the legacy paths?
    pages = [f for f in os.listdir(ROOT) if f.endswith(('.dc.html', '.html'))]
    refs = defaultdict(list)
    contents = {}
    for pg in pages:
        try:
            contents[pg] = open(os.path.join(ROOT, pg)).read()
        except Exception:
            continue
        for lp in pairs:
            if '/' + lp in contents[pg]:
                refs[lp].append(pg)

    for lp, (mp, d) in sorted(pairs.items()):
        used = f'{len(refs[lp])} page(s)' if refs[lp] else 'unreferenced'
        print(f'  {lp:<52} -> {mp:<52} d={d:.2f}  {used}')
    if orphans:
        print('\nUNMATCHED (kept as-is, review manually):')
        for lp, why in orphans:
            print(f'  {lp:<52} {why}')

    if args.dry_run:
        print('\n--dry-run: nothing written')
        return

    rewrites = 0
    for pg, text in contents.items():
        new = text
        for lp, (mp, _) in pairs.items():
            new = new.replace('/' + lp, '/' + mp)
        if new != text:
            open(os.path.join(ROOT, pg), 'w').write(new)
            rewrites += 1

    removed = 0
    for lp in pairs:
        try:
            os.remove(os.path.join(ROOT, lp))
            removed += 1
        except OSError as e:
            print(f'  !! could not remove {lp}: {e}', file=sys.stderr)

    print(f'\nrewrote {rewrites} pages, removed {removed} superseded files')


if __name__ == '__main__':
    main()
