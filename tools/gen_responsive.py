#!/usr/bin/env python3
"""Generate responsive image derivatives and wire them into the pages.

The mirrored Squarespace assets are single files sized for a 1440px desktop —
the CDN only ever returned WebP capped at 2500px, so that is what every visitor
got, phone included. /beyond-ayahuasca shipped 5.8MB of images to a 390px
screen. This produces a width ladder per image under assets/r/ and rewrites each
<img> with a srcset, a measured sizes, intrinsic width/height and lazy-loading.

Masters are never touched: assets/ stays exactly as sync_assets.py left it, and
`src` still points at the master, so anything that cannot read a srcset gets
what it got before.

    python3 tools/gen_responsive.py --report   # what would change
    python3 tools/gen_responsive.py            # generate + rewrite (idempotent)
    python3 tools/gen_responsive.py --clean    # delete assets/r/ and unwire

`sizes` comes from tools/image-sizes.json, which records the width each image
actually renders at in each of the three layout regimes (phone / collapsed /
desktop), measured in a headless browser rather than guessed from the markup.
Re-measure with the probe in the session scratchpad if the layout moves.

Run this AFTER tools/migrate_blog.py — that regenerates Blog*.dc.html from
scratch and would drop the attributes this adds.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
DERIV = os.path.join(ASSETS, 'r')
SIZES_FILE = os.path.join(ROOT, 'tools', 'image-sizes.json')

# The steps a derivative may be generated at. Anything wider than the image is
# ever asked to fill (at 2x) is pointless, and anything below 320 is narrower
# than the smallest phone.
LADDER = [320, 480, 640, 800, 1080, 1280, 1600, 2000]
QUALITY = 82

IMG_TAG = re.compile(r'<img\b[^>]*>', re.S)
ATTR = re.compile(r'(\w[\w-]*)\s*=\s*"([^"]*)"', re.S)
# Attributes this tool owns; any previous run's values are replaced wholesale.
MANAGED = ('srcset', 'sizes', 'width', 'height', 'decoding')


def load_sizes():
    if not os.path.exists(SIZES_FILE):
        sys.exit('missing %s — measure the pages first (see the docstring)' % SIZES_FILE)
    return json.load(open(SIZES_FILE))


def derivative_rel(src, w):
    """/assets/home/home-01.webp + 800 -> assets/r/home/home-01-800w.webp"""
    rel = src[len('/assets/'):]
    stem, _ = os.path.splitext(rel)
    return os.path.join('assets', 'r', stem + '-%dw.webp' % w)


def targets_for(nat, needed):
    """Ladder steps to generate: everything up to what the image is asked to
    fill at 2x, capped at its own resolution. The master covers the top end."""
    cap = min(nat, needed)
    out = [w for w in LADDER if w < nat and w <= cap]
    if not out and nat > LADDER[0]:
        out = [min(LADDER[0], nat)]
    return out


def build(sizes, report=False):
    try:
        from PIL import Image
    except ImportError:
        sys.exit('Pillow is required: python3 -m pip install pillow')

    made = skipped = 0
    saved = 0
    for src, info in sorted(sizes.items()):
        master = os.path.join(ROOT, src.lstrip('/'))
        if not os.path.exists(master):
            print('  missing master:', src)
            continue
        nat = info['nat']
        needed = max(info['w390'], info['w900'], info['w1440']) * 2
        wanted = targets_for(nat, needed)
        if not wanted:
            continue
        im = None
        for w in wanted:
            rel = derivative_rel(src, w)
            out = os.path.join(ROOT, rel)
            if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(master):
                skipped += 1
                continue
            if report:
                print('  would write', rel)
                made += 1
                continue
            if im is None:
                im = Image.open(master)
                im = im.convert('RGBA' if 'A' in im.getbands() else 'RGB')
            h = max(1, round(im.height * w / im.width))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            im.resize((w, h), Image.LANCZOS).save(out, 'WEBP', quality=QUALITY, method=6)
            made += 1
        if im is not None:
            im.close()
    return made, skipped


def srcset_for(src, info):
    nat = info['nat']
    needed = max(info['w390'], info['w900'], info['w1440']) * 2
    entries = []
    for w in targets_for(nat, needed):
        rel = derivative_rel(src, w)
        if os.path.exists(os.path.join(ROOT, rel)):
            entries.append('/%s %dw' % (rel.replace(os.sep, '/'), w))
    # The master closes the ladder, but only when a high-DPR screen could
    # genuinely use it — otherwise a 3x phone would pull 2500px for a 350px slot.
    if nat <= needed * 1.15:
        entries.append('%s %dw' % (src, nat))
    return ', '.join(entries)


def sizes_for(info):
    """A fluid element is declared in vw, a capped one in px.

    Below 640 the layout is fluid, so the phone width is a fraction of the
    viewport. Between 641 and 1180 .pt-fluid is capped at 720px regardless of
    viewport, so a px value is the accurate declaration there — except for
    full-bleed section backgrounds, which really are 100vw. Above 1180 the
    content column is fixed, so px again."""
    parts = []
    phone_vw = min(100, -(-info['w390'] * 100 // 390))  # ceil
    parts.append('(max-width:640px) %dvw' % phone_vw)
    if info['w900'] >= 855:
        parts.append('(max-width:1180px) 100vw')
    else:
        parts.append('(max-width:1180px) %dpx' % info['w900'])
    parts.append('%dpx' % info['w1440'])
    return ', '.join(parts)


def rewrite_tag(tag, sizes, first_in_file, clean=False):
    attrs = dict(ATTR.findall(tag))
    src = attrs.get('src', '')
    if not src.startswith('/assets/'):
        return tag, False
    info = sizes.get(src)
    if info is None:
        return tag, False

    # Strip whatever a previous run put there, then re-add.
    new = tag
    for a in MANAGED:
        # \s+ , not \s: a single-character bite leaves the attribute's newline
        # and indent behind, so every re-run stacked another blank line inside
        # the tag until the <img> was mostly whitespace.
        new = re.sub(r'\s+%s\s*=\s*"[^"]*"' % a, '', new, flags=re.S)
    if clean:
        return (new, new != tag)

    add = []
    ss = srcset_for(src, info)
    if ss:
        add.append('srcset="%s"' % ss)
        add.append('sizes="%s"' % sizes_for(info))
    if info.get('nat') and info.get('natH'):
        add.append('width="%d"' % info['nat'])
        add.append('height="%d"' % info['natH'])
    add.append('decoding="async"')
    if not add:
        return tag, False

    # Insert straight after the src attribute so the tag stays readable.
    m = re.search(r'src\s*=\s*"[^"]*"', new, re.S)
    new = new[:m.end()] + '\n           ' + '\n           '.join(add) + new[m.end():]

    # Anything with no loading attribute at all gets lazy, except the first
    # image on the page — that one is nearly always the hero, and lazy-loading
    # the largest-contentful element delays it rather than saving anything.
    if 'loading=' not in new:
        if first_in_file:
            new = new[:-1].rstrip() + ' loading="eager" fetchpriority="high">'
        else:
            new = new[:-1].rstrip() + ' loading="lazy">'
    elif first_in_file and 'loading="eager"' in new and 'fetchpriority' not in new:
        new = new.replace('loading="eager"', 'loading="eager" fetchpriority="high"')
    return new, True


def rewrite_pages(sizes, clean=False, report=False):
    changed = 0
    for fn in sorted(os.listdir(ROOT)):
        if not fn.endswith('.dc.html'):
            continue
        path = os.path.join(ROOT, fn)
        text = open(path).read()
        seen = [0]

        def sub(m):
            first = seen[0] == 0
            seen[0] += 1
            new, did = rewrite_tag(m.group(0), sizes, first, clean)
            return new

        out = IMG_TAG.sub(sub, text)
        if out != text:
            changed += 1
            if report:
                print('  would rewrite', fn)
            else:
                open(path, 'w').write(out)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', action='store_true', help='show what would change')
    ap.add_argument('--clean', action='store_true', help='remove derivatives and unwire pages')
    args = ap.parse_args()
    sizes = load_sizes()

    if args.clean:
        n = rewrite_pages(sizes, clean=True)
        import shutil
        if os.path.exists(DERIV):
            shutil.rmtree(DERIV)
        print('removed assets/r/, unwired %d pages' % n)
        return

    print('Generating derivatives…')
    made, skipped = build(sizes, report=args.report)
    print('  %d written, %d already current' % (made, skipped))
    print('Wiring pages…')
    n = rewrite_pages(sizes, report=args.report)
    print('  %d pages %s' % (n, 'would change' if args.report else 'rewritten'))

    if not args.report and os.path.exists(DERIV):
        tot = sum(os.path.getsize(os.path.join(dp, f))
                  for dp, _, fs in os.walk(DERIV) for f in fs)
        cnt = sum(len(fs) for _, _, fs in os.walk(DERIV))
        print('assets/r/: %d files, %.1f MB' % (cnt, tot / 1024 / 1024))


if __name__ == '__main__':
    main()
