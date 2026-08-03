#!/usr/bin/env python3
"""Mirror every Squarespace-hosted asset into assets/ with stable names.

Squarespace serves uploads from a CDN under names we don't control: some are
meaningful ("Maloka_Interior-...jpg"), many are not ("image-asset.jpeg" five
times over, bare UUIDs, epoch-millisecond hashes). This script gives every
asset one deterministic local name, records where it came from, and can be
re-run at any time to pick up new uploads without re-downloading the rest.

    python3 tools/sync_assets.py            # sync everything
    python3 tools/sync_assets.py --force    # re-download even if present
    python3 tools/sync_assets.py --report   # inventory only, no downloads

Assets land in assets/<section>/<slug>.<ext> and every one is recorded in
assets/manifest.json:

    { "<cdn-url-without-query>": {
        "local": "assets/home/hero-amazon.jpg",
        "original_name": "IMG_2068.jpg",
        "pages": ["/", "/discoverpaititi"],
        "alt": "...", "bytes": 812345, "sha256": "..." } }

Downloads request ?format=original, so these are the full-resolution masters —
crop and resize locally rather than re-fetching at a different ?format=.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
MANIFEST = os.path.join(ASSETS, 'manifest.json')
SITE = 'https://paititi-institute.org'

# route -> the assets/<section>/ folder its images belong to
ROUTES = OrderedDict([
    ('/', 'home'),
    ('/discoverpaititi', 'home'),
    ('/about-us', 'about'),
    ('/team', 'about'),
    ('/press-media', 'about'),
    ('/contact', 'about'),
    ('/retreats', 'retreats'),
    ('/online-courses', 'retreats'),
    ('/beyond-ayahuasca', 'retreats'),
    ('/initiatives', 'initiatives'),
    ('/initiatives/yagua-cultural-heritage-center-indigenous-school', 'initiatives'),
    ('/initiatives/project-one-f5w4d-4nex6', 'initiatives'),
    ('/store', 'store'),
    ('/store/p/us-tour-rsvp-donation', 'store'),
    ('/blog', 'blog'),
    ('/terms-conditions', 'legal'),
    ('/who/privacy-policy', 'legal'),
])

# Blog posts carry most of the photography; each body image needs mirroring too.
BLOG_POSTS = [
    'how-to-create-sustainable-relationships-for-living-in-community',
    'a-living-rite-of-passage-into-the-forgotten-kingdoms-of-the-amazon-rainforest',
    'cant-blame-the-chaos-a-path-less-traveled-in-perilous-times',
    'integration-phenomenal-into-mundane',
    'makes-life-worth-living-in-a-time-turmoil',
    'shards-shattered-ego-reflecting-countless-arms-compassion',
    'embody-true-nature-healing-retreat',
]
for _slug in BLOG_POSTS:
    ROUTES['/blog/' + _slug] = 'blog'

# Names that carry no information — such assets get named from their context.
GENERIC = re.compile(
    r'^(image-asset|unnamed|untitled|download|photo|img|image)'
    r'|^[0-9a-f]{8}-[0-9a-f]{4}-'          # bare UUID
    r'|^\d{10,}'                            # epoch-millisecond hash
    r'|^[A-Z0-9]{16,}$',                    # Squarespace upload token
    re.I)

CDN = re.compile(r'https://images\.squarespace-cdn\.com/content/v1/[^"\'\\\s)>]+')

# Real format from magic bytes: Squarespace happily serves WebP under a .jpg name.
SIGNATURES = [
    (b'\xff\xd8\xff', 'jpg'), (b'\x89PNG\r\n\x1a\n', 'png'), (b'GIF8', 'gif'),
    (b'\x00\x00\x01\x00', 'ico'), (b'%PDF', 'pdf'), (b'<svg', 'svg'), (b'<?xml', 'svg'),
]


def fetch(url, binary=True):
    """curl, not urllib — the local python has no SSL root certificates."""
    res = subprocess.run(
        ['curl', '-fsSL', '--max-time', '120', '-A', 'Mozilla/5.0 (asset sync)', url],
        capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f'curl {res.returncode}: {url}')
    return res.stdout if binary else res.stdout.decode('utf-8', 'replace')


def real_ext(data, fallback):
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    for sig, ext in SIGNATURES:
        if data[:len(sig)] == sig:
            return ext
    return fallback


def slugify(s):
    s = unquote(s)
    s = re.sub(r'\.[A-Za-z0-9]+$', '', s)          # strip extension
    s = re.sub(r'[+_\s]+', '-', s)
    s = re.sub(r'[^A-Za-z0-9-]', '', s)
    s = re.sub(r'-{2,}', '-', s).strip('-').lower()
    return s[:60]


def clean_url(raw):
    """Normalize an extracted URL: unescape JSON slashes, drop query/entities."""
    u = raw.replace('\\u002F', '/').replace('\\/', '/')
    u = re.split(r'[?&"\'<>]|&quot;|&amp;', u)[0]
    return u.rstrip('.,);')


def extract(html, page):
    """Every CDN asset on a page, with alt text where the markup provides it."""
    found = OrderedDict()
    # <img> tags first: they carry alt text worth keeping.
    for tag in re.findall(r'<img\b[^>]*>', html, re.I):
        src = None
        for attr in ('data-src', 'src'):
            m = re.search(attr + r'\s*=\s*"([^"]+)"', tag, re.I)
            if m and 'squarespace-cdn' in m.group(1):
                src = clean_url(m.group(1))
                break
        if not src:
            continue
        alt = re.search(r'\balt\s*=\s*"([^"]*)"', tag, re.I)
        found.setdefault(src, alt.group(1).strip() if alt else '')
    # Then anything else (CSS backgrounds, JSON blobs, og:image, favicon).
    for m in CDN.finditer(html):
        found.setdefault(clean_url(m.group(0)), '')
    return found


def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            return json.load(f)
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='re-download assets already present')
    ap.add_argument('--report', action='store_true', help='inventory only, download nothing')
    args = ap.parse_args()

    manifest = load_manifest()
    # url -> {section, alt, pages}
    catalog = OrderedDict()

    print('Crawling live pages…')
    for route, section in ROUTES.items():
        try:
            html = fetch(SITE + route, binary=False)
        except Exception as e:
            print(f'  !! {route}: {e}', file=sys.stderr)
            continue
        hits = extract(html, route)
        for url, alt in hits.items():
            entry = catalog.setdefault(url, {'section': section, 'alt': '', 'pages': []})
            if alt and not entry['alt']:
                entry['alt'] = alt
            if route not in entry['pages']:
                entry['pages'].append(route)
        print(f'  {route:<62} {len(hits):>3} assets')

    print(f'\n{len(catalog)} unique assets referenced across {len(ROUTES)} pages')
    have = sum(1 for u in catalog if u in manifest and os.path.exists(os.path.join(ROOT, manifest[u]['local'])))
    print(f'{have} already mirrored, {len(catalog) - have} missing\n')

    if args.report:
        for url, meta in catalog.items():
            state = 'OK  ' if url in manifest else 'MISS'
            print(f'{state} [{meta["section"]:<11}] {url.rsplit("/", 1)[-1][:52]:<52} {",".join(meta["pages"][:2])}')
        return

    used_names = {m['local'] for m in manifest.values()}
    counters = {}
    downloaded = skipped = failed = 0

    for url, meta in catalog.items():
        section = meta['section']
        prior = manifest.get(url)
        if prior and not args.force and os.path.exists(os.path.join(ROOT, prior['local'])):
            skipped += 1
            continue

        original = url.rsplit('/', 1)[-1]
        base = slugify(original)
        if not base or GENERIC.match(original):
            # No usable name on the CDN — derive one from where it's used.
            page = meta['pages'][0].strip('/').replace('/', '-') or 'home'
            counters[page] = counters.get(page, 0) + 1
            base = f'{page}-{counters[page]:02d}'

        try:
            data = fetch(url + '?format=original')
        except Exception as e:
            print(f'  !! {original}: {e}', file=sys.stderr)
            failed += 1
            continue

        ext = real_ext(data, original.rsplit('.', 1)[-1].lower() if '.' in original else 'jpg')
        rel = f'assets/{section}/{base}.{ext}'
        n = 2
        while rel in used_names and (not prior or prior['local'] != rel):
            rel = f'assets/{section}/{base}-{n}.{ext}'
            n += 1
        used_names.add(rel)

        path = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)

        manifest[url] = {
            'local': rel,
            'original_name': original,
            'pages': meta['pages'],
            'alt': meta['alt'],
            'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()[:16],
        }
        downloaded += 1
        print(f'  + {rel:<52} {len(data)//1024:>6} KB   ← {original[:40]}')

    with open(MANIFEST, 'w') as f:
        json.dump(OrderedDict(sorted(manifest.items())), f, indent=2)

    total = sum(m['bytes'] for m in manifest.values())
    print(f'\ndownloaded {downloaded} · skipped {skipped} · failed {failed}')
    print(f'manifest: {len(manifest)} assets, {total/1024/1024:.1f} MB → assets/manifest.json')


if __name__ == '__main__':
    main()
