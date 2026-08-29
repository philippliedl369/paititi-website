#!/usr/bin/env python3
"""One-time migration: pull the Paititi blog out of Squarespace and generate
static .dc.html pages (index, category pages, one page per post).

Usage:  python3 tools/migrate_blog.py
Re-run safe: overwrites generated files, skips already-downloaded images.
Prints the _redirects and sitemap lines to merge afterwards.
"""
import hashlib
import html.parser
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://paititi-institute.org'
ASSET_DIR = os.path.join(ROOT, 'assets', 'blog')
SITE_TZ = timezone(timedelta(hours=-5))  # Lima; matches displayed M/D/YY dates

CATEGORY_SLUGS = {
    'Health & Wellness': 'health-wellness',
    'Indigenous Traditions': 'indigenous-traditions',
    'Plant Medicine': 'plant-medicine',
    'Transformation': 'transformation',
}

# --- Languages --------------------------------------------------------------
# The generator renders one source (data/blog/posts.json) into two trees. Only
# the values that actually differ live here; everything structural — the fluid
# grid coordinates, the CSS, the card markup — is shared, so a layout change is
# made once and both languages get it.
#
# The English entry has to reproduce the committed pages byte for byte; that is
# what `--check` verifies, and it is the only guarantee that the snapshot the
# posts were recovered into is faithful.
#
# hreflang, <link rel=alternate> and the header's `sister` prop are deliberately
# NOT set here: tools/apply_hreflang.py owns those for every page on the site,
# blog pages included, and two owners would drift.
LANGS = {
    'en': {
        'html_lang': 'en',
        'file_suffix': '',                 # BlogPost-<slug>.dc.html
        'header': 'SiteHeader',
        'footer': 'SiteFooter',
        'blog_base': '/blog',
        'cat_base': '/blog/category',
        'team_href': '/team',
        'index_file': 'Blog.dc.html',
        'cat_file': 'BlogCategory-{cslug}.dc.html',
        'post_file': 'BlogPost-{slug}.dc.html',
        'index_title': 'Journal',
        'cat_title': '{name} — Journal',
        'hero_title': 'Living Transmissions',
        'hero_lede': ('A living space where ancient wisdom meets modern insight to inspire your '
                      'journey toward personal and planetary transformation. Here, we share stories, '
                      'reflections, and practical guidance rooted in indigenous traditions, '
                      'ecological stewardship, and conscious living.'),
        'meta_desc': ('A living space where ancient wisdom meets modern insight to inspire your '
                      'journey toward personal and planetary transformation.'),
        'substack': ('<strong>Look for more articles with Romans Substack page </strong>'
                     '<a href="https://substack.com/@romanhanis?utm_source=global-search" '
                     'target="_blank" rel="noopener"><strong>HERE</strong></a>'),
        'hero_alt': 'Gathering at the Paititi retreat centre',
        'eyes_alt': 'Stylized Buddha eyes over water with lotus petals',
        'read_more': 'Read More',
        'previous': 'Previous',
        'next': 'Next',
        'more_entries': 'More journal entries',
        'brand': 'Paititi Institute',
        # Identity maps: English slugs are the ones in the snapshot.
        'post_slugs': {},
        'cat_slugs': {},
    },
    'es': {
        'html_lang': 'es',
        'file_suffix': '.es',              # BlogPost-<slug>.es.dc.html
        'header': 'SiteHeader.es',
        'footer': 'SiteFooter.es',
        'blog_base': '/es/diario',
        'cat_base': '/es/diario/categoria',
        'team_href': '/es/equipo',
        'index_file': 'Blog.es.dc.html',
        'cat_file': 'BlogCategory-{cslug}.es.dc.html',
        'post_file': 'BlogPost-{slug}.es.dc.html',
        'index_title': 'Diario',
        'cat_title': '{name} — Diario',
        'hero_title': 'Transmisiones Vivas',
        'hero_lede': ('Un espacio vivo donde la sabiduría ancestral se encuentra con la mirada '
                      'contemporánea para inspirar tu camino hacia la transformación personal y '
                      'planetaria. Aquí compartimos historias, reflexiones y orientación práctica '
                      'enraizadas en las tradiciones indígenas, el cuidado de la tierra y una vida '
                      'consciente.'),
        'meta_desc': ('Un espacio vivo donde la sabiduría ancestral se encuentra con la mirada '
                      'contemporánea para inspirar tu camino hacia la transformación personal y '
                      'planetaria.'),
        'substack': ('<strong>Encuentra más artículos en la página de Substack de Roman </strong>'
                     '<a href="https://substack.com/@romanhanis?utm_source=global-search" '
                     'target="_blank" rel="noopener"><strong>AQUÍ</strong></a>'),
        'hero_alt': 'Encuentro en el centro de retiros de Paititi',
        'eyes_alt': 'Ojos de Buda estilizados sobre el agua, con pétalos de loto',
        'read_more': 'Seguir leyendo',
        'previous': 'Anterior',
        'next': 'Siguiente',
        'more_entries': 'Más entradas del diario',
        'brand': 'Instituto Paititi',
        # Filled from data/blog/es.json at load time.
        'post_slugs': {},
        'cat_slugs': {},
    },
}


def fetch(url):
    # curl instead of urllib: the local python install lacks SSL root certs.
    import subprocess
    res = subprocess.run(
        ['curl', '-fsSL', '--max-time', '60', '-A', 'Mozilla/5.0 (site migration)', url],
        capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f'curl failed ({res.returncode}) for {url}: {res.stderr.decode()[:200]}')
    return res.stdout


def fetch_json(url):
    return json.loads(fetch(url + ('&' if '?' in url else '?') + 'format=json'))


def strip_tags(s):
    s = re.sub(r'<[^>]+>', '', s or '')
    return html_unescape(s).strip()


def html_unescape(s):
    import html as h
    return h.unescape(s or '')


def slug_of(item):
    return item['urlId'].split('/')[-1]


def display_date(item):
    """The site shows M/D/YY; the ISO form goes into <time datetime>."""
    dt = datetime.fromtimestamp(item['publishOn'] / 1000, tz=SITE_TZ)
    return f'{dt.month}/{dt.day}/{dt.strftime("%y")}', dt.strftime('%Y-%m-%d')


IMG_TAG = re.compile(r'<img\b[^>]*>', re.I)
ATTR = lambda name: re.compile(name + r'\s*=\s*"([^"]*)"', re.I)
MANIFEST = os.path.join(ROOT, 'assets', 'manifest.json')

_manifest = None


def manifest():
    """assets/manifest.json, keyed by the origin CDN URL (see sync_assets.py)."""
    global _manifest
    if _manifest is None:
        try:
            with open(MANIFEST) as f:
                _manifest = json.load(f)
        except FileNotFoundError:
            _manifest = {}
    return _manifest


def save_manifest():
    if _manifest:
        with open(MANIFEST, 'w') as f:
            json.dump(dict(sorted(_manifest.items())), f, indent=2)


def slugify(s):
    s = urllib.parse.unquote(s)
    s = re.sub(r'\.[A-Za-z0-9]+$', '', s)
    s = re.sub(r'[+_\s]+', '-', s)
    s = re.sub(r'[^A-Za-z0-9-]', '', s)
    return re.sub(r'-{2,}', '-', s).strip('-').lower()[:60]


def localize_images(body, slug, page_url):
    """Point every squarespace-cdn image at its mirrored copy.

    tools/sync_assets.py has already mirrored most of these — as WebP, keyed in
    assets/manifest.json by the same CDN URL that appears here — so look the URL
    up first and only fetch what is genuinely missing. Downloading unconditionally
    is what produced 8MB of .jpg duplicating .webp the repo already had.
    """
    os.makedirs(ASSET_DIR, exist_ok=True)
    man = manifest()
    have = {m['local'] for m in man.values()}

    def repl(m):
        tag = m.group(0)
        src = None
        for attr in ('data-src', 'src'):
            am = ATTR(attr).search(tag)
            if am and 'squarespace-cdn.com' in am.group(1):
                src = am.group(1)
                break
        if not src:
            return ''  # drop placeholder/tracking imgs without a CDN source
        url = src.split('?')[0]
        alt_m = ATTR('alt').search(tag)
        alt = alt_m.group(1) if alt_m else ''

        entry = man.get(url)
        if entry and os.path.exists(os.path.join(ROOT, entry['local'])):
            rel = entry['local']
            if page_url not in entry.get('pages', []):
                entry.setdefault('pages', []).append(page_url)
        else:
            original = url.rsplit('/', 1)[-1]
            base = slugify(original) or f'{slug}-img'
            ext = original.rsplit('.', 1)[-1].lower() if '.' in original else 'jpg'
            if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
                ext = 'jpg'
            rel = f'assets/blog/{base}.{ext}'
            n = 2
            while rel in have:
                rel = f'assets/blog/{base}-{n}.{ext}'
                n += 1
            try:
                data = fetch(url + '?format=1200w')
            except Exception as e:
                print(f'    !! image failed {url}: {e}', file=sys.stderr)
                return ''
            with open(os.path.join(ROOT, rel), 'wb') as f:
                f.write(data)
            have.add(rel)
            man[url] = {'local': rel, 'original_name': original, 'pages': [page_url],
                        'alt': alt, 'bytes': len(data),
                        'sha256': hashlib.sha256(data).hexdigest()[:16]}
            print(f'    + {rel} ({len(data)//1024} KB)')

        return f'<img src="/{rel}" alt="{alt}" loading="lazy">'

    return IMG_TAG.sub(repl, body)


def clean_body(body, slug, page_url):
    body = re.sub(r'<script\b.*?</script>', '', body, flags=re.S | re.I)
    body = re.sub(r'<noscript\b.*?</noscript>', '', body, flags=re.S | re.I)
    body = re.sub(r'</?gen-text[^>]*>', '', body)
    body = localize_images(body, slug, page_url)
    # Unwrap squarespace block scaffolding into plain divs (keeps nesting valid).
    body = re.sub(r'\sdata-[a-zA-Z-]+="[^"]*"', '', body)
    body = re.sub(r'\scontenteditable="[^"]*"', '', body)
    # Squarespace-era links that don't exist here: /events was the old events
    # page, and "#/events" is its hash-router spelling.
    body = body.replace('href="/retreats#/events"', 'href="/retreats#events"')
    body = body.replace('href="/events"', 'href="/retreats#events"')
    return body


PAGE_TEMPLATE = '''<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/favicon.ico" sizes="any">
<script src="/support.js"></script>
<script src="/anchor-scroll.js" defer></script>
</head>
<body>
<x-dc>
<helmet>
<title>{title} | {brand}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title} | {brand}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Paititi Institute">
<meta property="article:published_time" content="{iso_date}">
<meta name="theme-color" content="#2A1736">
<link rel="icon" href="/assets/brand/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/fonts.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/colors.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/typography.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/spacing.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/effects.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/styles.css">
<link rel="stylesheet" href="/paititi.css">
<script src="/_ds/meristem-design-system/_ds_bundle.js"></script>
<style>
  {css}
</style>
</helmet>
<div class="pt-page">
<dc-import name="{header}" active="journal" hint-size="100%,209px"></dc-import>
<main>

  <section class="pt-sec pt-sec-flat bp-sec">
    <div class="pt-sec-bg"></div>
    <article class="bp-item">
      <h1>{title}</h1>
      <p class="bp-meta">{cats_line}<a class="bp-author" href="{team_href}">{author}</a><time datetime="{iso_date}">{date}</time></p>
      <div class="bp-body pt-prose">
{body}
      </div>
    </article>
  </section>

  <nav class="bp-pager" aria-label="{more_entries}">
    {prev_link}
    {next_link}
  </nav>

</main>
<dc-import name="{footer}"></dc-import>
</div>
</x-dc>
</body>
</html>
'''

# The blog item template, measured off the live post pages: one near-black
# section, a 596px measure centred at x=422, reversed out white throughout.
POST_CSS = """
  .bp-sec{--pt-bg:#210416;color:#fff}
  .bp-item{max-width:596px;margin:0 auto;padding:266px 0 57.6px}
  .bp-sec h1,.bp-sec h2,.bp-sec h3,.bp-sec h4,.bp-sec p,.bp-sec li{color:#fff}
  /* The live title box carries 32px of padding as well as a 32px margin. */
  .pt-page .bp-sec h1{font-size:64px;line-height:1.232;margin:0 0 32px;padding-bottom:32px}

  /* Category chips and byline sit on one 14.272px line under the title. */
  .pt-page .bp-meta{display:flex;flex-wrap:wrap;gap:0 19px;margin:0;
    font-size:14.272px;font-weight:400;line-height:1.2;letter-spacing:normal}
  .bp-meta a{color:#fff;text-decoration:none}
  .bp-meta a:hover{text-decoration:underline}
  .bp-meta time{opacity:.8}
  /* The byline is a second meta group, set further from the categories. */
  .bp-meta .bp-author{margin-left:64px}

  .bp-body{margin:70px 0 44px}
  .bp-body img{max-width:100%;height:auto;display:block}
  /* Squarespace's own block scaffolding is preserved verbatim in the migrated
     body, so its spacing has to be reproduced rather than replaced. Rich text
     runs on a flat 16px paragraph rhythm and 32px around headings, with the
     first and last child of each run flush to the block. */
  .pt-page .bp-body .sqs-html-content > *{margin:16px 0}
  .pt-page .bp-body .sqs-html-content > h1,
  .pt-page .bp-body .sqs-html-content > h2,
  .pt-page .bp-body .sqs-html-content > h3,
  .pt-page .bp-body .sqs-html-content > h4{margin:32px 0}
  .pt-page .bp-body .sqs-html-content > *:first-child{margin-top:0}
  .pt-page .bp-body .sqs-html-content > *:last-child{margin-bottom:0}
  .pt-page .bp-body .sqs-html-content ul,
  .pt-page .bp-body .sqs-html-content ol{padding-left:40px}
  .pt-page .bp-body .sqs-html-content li{margin-bottom:8.8px}

  /* An image block is an aspect-ratio box: the container reserves the height
     with padding-bottom and the image is taken out of flow inside it. Leaving
     the image in flow doubles the height — the container's padding *plus* the
     image's intrinsic height — which is what made post bodies run long. */
  .bp-body figure{margin:0}
  /* An image block's caption is a rich-text paragraph and carries the same 16px
     rhythm as body copy; the quote block sets its own measure and type. */
  .pt-page .bp-body .image-caption p{margin:16px 0 0}
  .bp-body .sqs-quote-block-contents{margin:17.6px 0}
  .pt-page .bp-body blockquote{margin:0;font-size:19.2px;line-height:34.56px}
  .pt-page .bp-body figcaption.source{font-size:14.272px;font-weight:400;
    line-height:17.1264px;letter-spacing:normal}
  .bp-body .image-block-wrapper{position:relative;overflow:hidden}
  .bp-body .sqs-image-shape-container-element{position:relative;overflow:hidden}
  .bp-body .has-aspect-ratio > img{position:absolute;inset:0;
    width:100%;height:100%;max-width:none;object-fit:cover;display:block}
  /* The other variant, content-fit, has no reserved ratio: the image keeps its
     own height and must stay in flow or the block collapses to nothing. */
  .bp-body .content-fit > img{position:relative;width:100%;height:auto;display:block}

  /* Squarespace gutters every block with 17px of padding and pulls the row out
     by the same amount, so the text still lands on the 596px measure while the
     blocks themselves are 630px wide. Reproducing the gutter is what supplies
     the 17px between consecutive blocks and the right width for a half-width
     float — 315px, not 280px. */
  .bp-body .sqs-row{margin:0 -17px}
  .bp-body .sqs-block{padding:17px}
  .bp-body .float-right{float:right;width:50%}
  .bp-body .float-left{float:left;width:50%}
  .bp-body .sqs-row::after{content:"";display:table;clear:both}
  .bp-body a{color:#fff;text-decoration:underline;text-underline-offset:3px}

  /* Button blocks: the light variant, white on the near-black ground. */
  .bp-body .sqs-block-button-container{display:flex}
  .bp-body .sqs-block-button-container--center{justify-content:center}
  .bp-body .sqs-block-button-container--right{justify-content:flex-end}
  .pt-page .bp-body .sqs-block-button-element{display:block;padding:19.2px 38.4768px;
    background:#fff;color:#000;border-radius:16px 0;text-decoration:none;
    font-size:19.2px;font-weight:700;line-height:23.04px;letter-spacing:.384px}
  .pt-page .bp-body .sqs-block-button-element:hover{background:#F1EAF6;color:#000}
  .pt-page .bp-body h2{font-size:41.6px;line-height:1.3104}
  .pt-page .bp-body h3{font-size:28.8px;line-height:1.3552}

  /* Previous / next: two half-width targets on the same dark ground, each a
     chevron beside a two-line title set solid at 28.8px. */
  .bp-pager{display:flex;background:#210416;padding:43.2px 57.6px}
  .bp-pager a{flex:1 1 0;min-width:0;display:flex;align-items:center;
    text-decoration:none;color:#fff}
  .bp-pager .bp-pager-icon{flex:none;width:18px;height:32px;display:block}
  .bp-pager .bp-prev .bp-pager-icon{padding-right:25px;box-sizing:content-box}
  .bp-pager .bp-next .bp-pager-icon{padding-left:25px;box-sizing:content-box}
  .bp-pager .bp-pager-icon svg{width:18px;height:32px;display:block}
  .bp-pager .bp-pager-title{flex:1 1 auto;min-width:0}
  /* Present for screen readers; the chevron is the visible cue. */
  .bp-pager .bp-pager-label{position:absolute;width:1px;height:1px;overflow:hidden;
    clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap}
  .pt-page .bp-pager h2{font-family:var(--font-display);font-weight:400;font-size:28.8px;
    line-height:28.8px;color:#fff;margin:0;letter-spacing:normal}

  @media (max-width:1180px){
    .bp-item{padding:calc(var(--pt-header-h-live,var(--pt-header-h,209px)) + 57px) 24px 57.6px}
    .bp-body .sqs-row{margin:0}
    .bp-body .float-right,.bp-body .float-left{float:none;width:100%}
    .pt-page .bp-sec h1{font-size:40px}
    .pt-page .bp-body h2{font-size:30px}
    .bp-pager{flex-direction:column;gap:28px;padding:36px 24px}
  }
  @media (max-width:640px){
    .bp-item{padding:calc(var(--pt-header-h-live,var(--pt-header-h,124px)) + 36px) 20px 44px}
    .pt-page .bp-sec h1{font-size:34px;margin:0 0 24px;padding-bottom:24px}
    .pt-page .bp-body h2{font-size:27px}
    .pt-page .bp-body h3{font-size:22px}
    .bp-body{margin:40px 0 32px}
    /* 14.272px is under the readable floor, and the 64px byline offset is a
       desktop measurement that on one column just strands the name. */
    .pt-page .bp-meta{font-size:15px;gap:4px 16px}
    .bp-meta .bp-author{margin-left:0}
    /* Squarespace's 17px block gutter costs 34px of an already narrow measure;
       the horizontal half goes, the vertical rhythm stays. */
    .bp-body .sqs-block{padding:17px 0}
    .pt-page .bp-body blockquote{font-size:17.6px;line-height:1.7}
    .pt-page .bp-body .sqs-block-button-element{padding:16px 24px}
    .bp-pager{padding:32px 20px}
  }
  /* Body links sit in running prose, so they take padding only where a real
     finger is doing the tapping. */
  @media (pointer:coarse){
    .bp-meta a{display:inline-block;padding:5px 0}
  }
  /* The footer wave must match this page's final section colour. */
  footer.pt-footer{--pt-footer-wave:#210416}
"""


def cat_name(raw):
    return html_unescape(raw)


def cat_href(lang, cslug):
    """Category URL in `lang`'s tree, from the English category slug."""
    return lang['cat_base'] + '/' + lang['cat_slugs'].get(cslug, cslug)


def post_href(lang, slug):
    """Post URL in `lang`'s tree, from the English post slug."""
    return lang['blog_base'] + '/' + lang['post_slugs'].get(slug, slug)


TAG_SPLIT = re.compile(r'(<[^>]+>)')


def localize_links(body, lang):
    """Repoint internal links inside a post body at `lang`'s tree.

    Post bodies are Squarespace content and carry their own <a href> — five of
    them link to /retreats#events. Text-node translation never touches
    attributes, so without this a Spanish post would drop the reader back into
    the English site mid-article. The map is read from tools/i18n_pairs.json so
    it cannot disagree with _redirects or with the hreflang pairs.
    """
    if lang['html_lang'] == 'en':
        return body
    pairs = link_map()
    def one(m):
        href = m.group(1)
        path, _, frag = href.partition('#')
        target = pairs.get(path)
        if not target:
            return m.group(0)
        return 'href="' + target + ('#' + frag if frag else '') + '"'
    return re.sub(r'href="(/[^"]*)"', one, body)


_link_map = None


def link_map():
    """English clean URL -> Spanish clean URL, from the shared pair table."""
    global _link_map
    if _link_map is None:
        path = os.path.join(ROOT, 'tools', 'i18n_pairs.json')
        with open(path, encoding='utf-8') as f:
            cfg = json.load(f)
        _link_map = {p['en']: p['es'] for p in cfg['pairs']}
    return _link_map


def translate_body(body, text_map):
    """Swap the text nodes of a post body, leaving every tag exactly as it is.

    The translation file holds text nodes rather than whole translated bodies,
    so the Spanish page keeps whatever markup the English one has — including
    Squarespace's nested block scaffolding, which POST_CSS is written against.
    A node with no entry is left in English, which is visible on the page and
    reported by `migrate_blog.py` rather than failing the build.

    <style> and <script> contents are text nodes too, and must never be
    translated: the post bodies carry per-block Squarespace CSS.
    """
    if not text_map:
        return body, 0, 0
    out, skip, done, total = [], False, 0, 0
    for part in TAG_SPLIT.split(body):
        if part.startswith('<'):
            tag = part.lower()
            if tag.startswith(('<style', '<script')):
                skip = True
            elif tag.startswith(('</style', '</script')):
                skip = False
            out.append(part)
            continue
        if skip or not part.strip():
            out.append(part)
            continue
        total += 1
        key = part.strip()
        if key in text_map:
            done += 1
            lead = part[:len(part) - len(part.lstrip())]
            tail = part[len(part.rstrip()):]
            out.append(lead + text_map[key] + tail)
        else:
            out.append(part)
    return ''.join(out), done, total


_body_stats = []


def post_page(lang, post, prev_post, next_post, tr):
    """One post page. `tr` is this post's translation record, {} for English."""
    slug = post['slug']
    title = tr.get('title', post['title'])
    body, done, total = translate_body(post['body'], tr.get('text', {}))
    body = localize_links(body, lang)
    if tr:
        _body_stats.append((slug, done, total))
    desc = tr.get('description', post['description'])

    cats_line = ''.join(
        '<a href="%s">%s</a>' % (cat_href(lang, c['slug']),
                                 cat_title(lang, c).replace('&', '&amp;'))
        for c in post['categories'])

    chevron = ('<span class="bp-pager-icon" aria-hidden="true">'
               '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">'
               '<polyline points="{points}"/></svg></span>')

    def link(other, label, cls):
        if not other:
            return '<span></span>'
        t = translations_for(lang, other['slug']).get('title', other['title'])
        # The visible cue is the chevron; the word itself is for assistive tech.
        icon = chevron.format(points='15 4 7 12 15 20' if cls == 'bp-prev' else '9 4 17 12 9 20')
        inner = (f'<span class="bp-pager-title"><span class="bp-pager-label">{label}</span>'
                 f'<h2>{t}</h2></span>')
        return (f'<a class="{cls}" href="{post_href(lang, other["slug"])}">'
                + (icon + inner if cls == 'bp-prev' else inner + icon) + '</a>')

    page = PAGE_TEMPLATE.format(
        html_lang=lang['html_lang'], header=lang['header'], footer=lang['footer'],
        team_href=lang['team_href'], more_entries=lang['more_entries'], brand=lang['brand'],
        title=title.replace('"', '&quot;'), description=desc,
        date=post['date'], iso_date=post['iso_date'], css=POST_CSS.strip(),
        author=post['author'], cats_line=cats_line, body=body,
        prev_link=link(next_post, lang['previous'], 'bp-prev'),
        next_link=link(prev_post, lang['next'], 'bp-next'))
    return lang['post_file'].format(slug=slug), page


def index_card(lang, card):
    """One card in the 2-up grid: image, 20px spacer, byline, title, excerpt."""
    if card['source_url']:
        # An external link-post (Roman's Substack). It has no page in either
        # tree, so both trees point at the same outside URL.
        href, target = card['source_url'], ' target="_blank" rel="noopener"'
        title, excerpt = card['title'], card['excerpt']
    else:
        tr = translations_for(lang, card['slug'])
        href, target = post_href(lang, card['slug']), ''
        title = tr.get('title', card['title'])
        excerpt = tr.get('excerpt', card['excerpt'])
    excerpt_html = f'<div class="bl-excerpt">{excerpt}</div>'
    return f'''        <article class="bl-card">
          <a class="bl-image" href="{href}"{target}><img src="/{card['thumb']}" alt="" loading="lazy"></a>
          <div class="bl-text">
            <p class="bl-meta"><span>{card['author']}</span><time datetime="{card['date']}">{card['date_display']}</time></p>
            <h2 class="bl-title"><a href="{href}"{target}>{title}</a></h2>
            {excerpt_html}
            <a class="bl-more" href="{href}"{target}>{lang['read_more']}</a>
          </div>
        </article>'''


INDEX_TEMPLATE = '''<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="/favicon.ico" sizes="any">
<script src="/support.js"></script>
<script src="/anchor-scroll.js" defer></script>
</head>
<body>
<x-dc>
<helmet>
<title>{page_title} | {brand}</title>
<meta name="description" content="{meta_desc}">
<meta property="og:title" content="{page_title} | {brand}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Paititi Institute">
<meta property="og:image" content="/assets/blog/69265356-2542807292472488-6841856973810434048-n.webp">
<meta name="theme-color" content="#2A1736">
<link rel="icon" href="/assets/brand/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/brand/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/fonts.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/colors.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/typography.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/spacing.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/effects.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/styles.css">
<link rel="stylesheet" href="/paititi.css">
<script src="/_ds/meristem-design-system/_ds_bundle.js"></script>
<style>
{css}
</style>
</helmet>
<div class="pt-page">
<dc-import name="{header}" active="journal" hint-size="100%,209px"></dc-import>
<main>

  <!-- ===== Hero ===== -->
  <section class="pt-sec pt-sec-flat pt-hero bl-hero">
    <div class="pt-sec-bg">
      <img src="/assets/blog/69265356-2542807292472488-6841856973810434048-n.webp" alt="{hero_alt}" loading="eager">
    </div>
    <div class="pt-fluid" style="--pt-grid-top:304px;--pt-grid-bot:124px;--pt-rows:16;--pt-row-h:25.8906px">
      <div class="pt-hero-panel pt-prose" style="grid-area:1 / 6 / 10 / 20">
        <h1><strong>{hero_title}</strong></h1>
        <p>{hero_lede}</p>
      </div>
      <div class="pt-fit" style="grid-area:9 / 10 / 15 / 16">
        <img src="/assets/brand/icon-vision-purpose.webp" alt="{eyes_alt}" loading="eager">
      </div>
    </div>
  </section>

  <!-- ===== Substack band ===== -->
  <section class="pt-sec bl-substack">
    <div class="pt-sec-bg">
      <img src="/assets/blog/unsplash-image-jwn0vkrklvk.webp" alt="" loading="lazy">
    </div>
    <div class="pt-fluid" style="--pt-grid-top:58px;--pt-grid-bot:124px;--pt-rows:12">
      <div class="pt-fit" style="grid-area:1 / 3 / 13 / 9">
        <img src="/assets/blog/screenshot-2025-12-03-at-115430-am.webp" alt="Substack" loading="lazy">
      </div>
      <div class="pt-prose pt-vc" style="grid-area:6 / 15 / 9 / 23">
        <p>{substack}</p>
      </div>
    </div>
  </section>

  <!-- ===== Entries ===== -->
  <section class="pt-sec bl-list">
    <div class="pt-sec-bg"></div>
    {filter_note}
    <div class="bl-grid">
{cards}
    </div>
  </section>

  <section class="pt-sec bl-list" style="height:55px">
    <div class="pt-sec-bg"></div>
  </section>

</main>
<dc-import name="{footer}"></dc-import>
</div>
</x-dc>
</body>
</html>
'''

# The index and the four category pages share one template. Measured off the
# live /blog: a 2-up grid of 512px cards inside the 1200px column, 57.6px
# padding, 60px column gap and 65px row gap, reversed out on near-black.
INDEX_CSS = '''
  .bl-hero{--pt-hero-h:1006px;--pt-bg:#210416;--pt-scrim:rgba(33,4,22,.49);--pt-hero-ink:#fff}
  .bl-hero .pt-hero-panel{background:rgba(88,67,100,.39)}
  .bl-hero h1,.bl-hero p{text-align:center}

  .bl-substack{--pt-bg:#fff;--pt-scrim:rgba(255,255,255,.15)}

  .bl-list{--pt-bg:#210416;color:#fff}
  .bl-list h1,.bl-list h2,.bl-list p{color:#fff}

  .bl-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
    /* Declared 57.6px on the original, but the cards bleed, so the
       effective gaps measure 43 above the first row and 73 below the last. */
    gap:65px 60px;max-width:1200px;margin:0 auto;padding:43px 57.6px 73px}
  .bl-card{display:flex;flex-direction:column}
  .bl-image{display:block;overflow:hidden}
  .bl-image img{width:100%;height:343px;object-fit:cover;display:block;transition:transform .4s ease}
  .bl-image:hover img{transform:scale(1.03)}
  /* Squarespace puts a fixed 20px spacer between the image and the text. */
  .bl-text{margin-top:20px}
  .pt-page .bl-meta{display:flex;gap:0 12px;margin:0;font-size:14.272px;font-weight:400;
    line-height:1.2;letter-spacing:normal}
  .bl-meta time{opacity:.8}
  .pt-page .bl-title{font-family:var(--font-display);font-weight:400;font-size:28.8px;line-height:1.4;
    letter-spacing:normal;margin:10px 0 0}
  .bl-title a{color:#fff;text-decoration:none}
  .bl-title a:hover{text-decoration:underline}
  .pt-page .bl-excerpt{margin-top:11px;font-size:14.272px;line-height:1.8;letter-spacing:1.14176px}
  .pt-page .bl-more{display:inline-block;padding:10.65px 0;font-size:14.272px;line-height:1.8;
    color:#fff;text-decoration:underline;text-underline-offset:4px}
  .pt-page .bl-filter{max-width:1200px;margin:0 auto;padding:57.6px 57.6px 0;font-size:17.6px}
  .bl-filter a{color:#fff}

  @media (max-width:1180px){
    .bl-hero h1{font-size:40px}
    .bl-grid{grid-template-columns:1fr;gap:48px;padding:48px 24px}
    .bl-image img{height:auto;aspect-ratio:3/2}
    .bl-filter{padding:48px 24px 0}
  }
  @media (max-width:640px){
    .bl-grid{gap:40px;padding:40px 20px}
    .bl-filter{padding:40px 20px 0;font-size:16px}
    /* The index is a list of things to choose between, and at 14.272px the
       excerpt and date were the smallest type on the site. */
    .pt-page .bl-meta{font-size:15px}
    .pt-page .bl-excerpt{font-size:16px;letter-spacing:1.28px}
    .pt-page .bl-more{font-size:16px}
    .pt-page .bl-title{font-size:24px}
  }
  @media (pointer:coarse){
    .bl-filter a{display:inline-block;padding:6px 0}
    .bl-meta a{display:inline-block;padding:5px 0}
  }
  /* The footer wave must match this page's final section colour. */
  footer.pt-footer{--pt-footer-wave:#210416}
'''


# --- Translations -----------------------------------------------------------
_translations = {}


def load_translations():
    """data/blog/es.json — Spanish copy, keyed by the English post slug.

    Missing keys fall back to English rather than failing, so a half-finished
    translation still produces a working page instead of blocking the build;
    `--check` reports what is still falling back.
    """
    path = os.path.join(ROOT, 'data', 'blog', 'es.json')
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f'  no {os.path.relpath(path, ROOT)} — Spanish tree will mirror English')
        return
    _translations['es'] = data.get('posts', {})
    LANGS['es']['post_slugs'] = data.get('post_slugs', {})
    LANGS['es']['cat_slugs'] = data.get('cat_slugs', {})
    LANGS['es']['cat_names'] = data.get('cat_names', {})


def translations_for(lang, slug):
    return _translations.get(lang['html_lang'], {}).get(slug, {})


def cat_title(lang, cat):
    """Display name of a category in `lang`."""
    return lang.get('cat_names', {}).get(cat['slug'], cat['name'])


def load_snapshot():
    path = os.path.join(ROOT, 'data', 'blog', 'posts.json')
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise SystemExit(
            'data/blog/posts.json is missing. The Squarespace feed this script was\n'
            'originally written against no longer exists, so the posts come from that\n'
            'snapshot now. Rebuild it from the committed English pages with:\n'
            '    python3 tools/blog_snapshot.py')


def render(lang_key, snap, write=True):
    """Render every blog page for one language. Returns {filename: html}."""
    lang = LANGS[lang_key]
    posts = snap['posts']
    # Newest first, matching the order the index cards are already in.
    order = [c['slug'] for c in snap['cards'] if c['slug']]
    by_slug = {p['slug']: p for p in posts}
    ordered = [by_slug[s] for s in order if s in by_slug]

    pages = {}
    for idx, post in enumerate(ordered):
        prev_post = ordered[idx + 1] if idx + 1 < len(ordered) else None   # older
        next_post = ordered[idx - 1] if idx > 0 else None                  # newer
        fname, html = post_page(lang, post, prev_post, next_post,
                                translations_for(lang, post['slug']))
        pages[fname] = html

    cards = '\n'.join(index_card(lang, c) for c in snap['cards'])
    pages[lang['index_file']] = INDEX_TEMPLATE.format(
        html_lang=lang['html_lang'], header=lang['header'], footer=lang['footer'],
        page_title=lang['index_title'], meta_desc=lang['meta_desc'], brand=lang['brand'],
        hero_title=lang['hero_title'], hero_lede=lang['hero_lede'],
        hero_alt=lang['hero_alt'], eyes_alt=lang['eyes_alt'],
        substack=lang['substack'], filter_note='', css=INDEX_CSS.strip(), cards=cards)

    for cname, cslug in CATEGORY_SLUGS.items():
        in_cat = [c for c in snap['cards'] if c['slug'] and any(
            k['slug'] == cslug for k in by_slug.get(c['slug'], {}).get('categories', []))]
        cards = '\n'.join(index_card(lang, c) for c in in_cat)
        display = lang.get('cat_names', {}).get(cslug, cname)
        # The live category pages show the filtered grid and nothing else —
        # no "showing X" banner — so don't invent one.
        pages[lang['cat_file'].format(cslug=cslug)] = INDEX_TEMPLATE.format(
            html_lang=lang['html_lang'], header=lang['header'], footer=lang['footer'],
            page_title=lang['cat_title'].format(name=display), meta_desc=lang['meta_desc'], brand=lang['brand'],
            hero_title=lang['hero_title'], hero_lede=lang['hero_lede'],
            hero_alt=lang['hero_alt'], eyes_alt=lang['eyes_alt'],
            substack=lang['substack'], filter_note='', css=INDEX_CSS.strip(), cards=cards)

    if write:
        for fname, html in pages.items():
            with open(os.path.join(ROOT, fname), 'w', encoding='utf-8') as f:
                f.write(html)
    return pages


def main():
    """Render data/blog/posts.json into the English and Spanish blog trees.

    This used to fetch from Squarespace; that feed is gone (see the module
    docstring). --check renders without writing and diffs against what is on
    disk, which is how the English tree is held to "byte-identical".
    """
    check = '--check' in sys.argv
    snap = load_snapshot()
    load_translations()

    def normalise(html, fname):
        """Strip what the *later* passes add, so --check compares this one's work.

        The blog pipeline is migrate_blog.py -> gen_responsive.py ->
        apply_hreflang.py -> apply_head_meta.py. The second wires
        srcset/sizes/width/height into every <img>; the third inserts a
        rel=alternate block and a `sister` prop; the fourth moves the title and
        the social card out of <helmet> and into the real <head>. Comparing raw
        output against a fully processed page would report all four as
        differences and make --check useless the moment the pipeline has been
        run once.

        The last one is *applied* rather than stripped: it is a pure function of
        the page, so running it over this pass's fresh output puts both sides in
        the same shape without this file having to know what it does.
        """
        def one_img(m):
            keep = re.findall(r'\b(?:src|alt|loading)="[^"]*"', m.group(0))
            return '<img ' + ' '.join(keep) + '>'
        html = re.sub(r'<img\b[^>]*>', one_img, html)
        html = re.sub(r'<!-- i18n:hreflang.*?<!-- /i18n:hreflang -->\n?', '', html, flags=re.S)
        html = re.sub(r'\s+sister="[^"]*"', '', html)
        # og:url is copied from the canonical, which the line above just took
        # out — so on a processed page it survives while this pass, which never
        # writes a canonical, cannot produce one.
        html = re.sub(r'[ \t]*<meta property="og:url"[^>]*>\n?', '', html)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from apply_head_meta import transform
        return transform(html, fname)

    failed = 0
    for key in ('en', 'es'):
        pages = render(key, snap, write=not check)
        if check:
            for fname, html in sorted(pages.items()):
                path = os.path.join(ROOT, fname)
                try:
                    on_disk = open(path, encoding='utf-8').read()
                except FileNotFoundError:
                    print(f'  [{key}] MISSING  {fname}')
                    failed += 1
                    continue
                if normalise(on_disk, fname) != normalise(html, fname):
                    print(f'  [{key}] DIFFERS  {fname}')
                    failed += 1
        else:
            print(f'  [{key}] wrote {len(pages)} pages')

    if check:
        print('  all generated pages match what is on disk' if not failed
              else f'  {failed} page(s) differ')
        return 1 if failed else 0

    # Text nodes still falling back to English are worth naming: a partly
    # translated post renders, but it renders half in the wrong language.
    if _body_stats:
        short = [(s, d, t) for s, d, t in _body_stats if d < t]
        if short:
            print('\n  Spanish text nodes still falling back to English:')
            for s, d, t in short:
                print(f'    {t - d:3} of {t:3} untranslated  {s}')
        else:
            print(f'\n  Spanish: every text node translated across {len(_body_stats)} posts')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
