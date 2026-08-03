#!/usr/bin/env python3
"""One-time migration: pull the Paititi blog out of Squarespace and generate
static .dc.html pages (index, category pages, one page per post).

Usage:  python3 tools/migrate_blog.py
Re-run safe: overwrites generated files, skips already-downloaded images.
Prints the _redirects and sitemap lines to merge afterwards.
"""
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
    dt = datetime.fromtimestamp(item['publishOn'] / 1000, tz=SITE_TZ)
    return f'{dt.month}/{dt.day}/{dt.strftime("%y")}', dt


IMG_TAG = re.compile(r'<img\b[^>]*>', re.I)
ATTR = lambda name: re.compile(name + r'\s*=\s*"([^"]*)"', re.I)


def localize_images(body, slug):
    """Download every squarespace-cdn image at 1200w and rewrite the tag."""
    os.makedirs(ASSET_DIR, exist_ok=True)
    counter = [0]

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
        alt_m = ATTR('alt').search(tag)
        alt = alt_m.group(1) if alt_m else ''
        counter[0] += 1
        name = f'{slug}-{counter[0]:02d}.jpg'
        path = os.path.join(ASSET_DIR, name)
        if not os.path.exists(path):
            try:
                data = fetch(src.split('?')[0] + '?format=1200w')
                with open(path, 'wb') as f:
                    f.write(data)
                print(f'    image {name} ({len(data)//1024} KB)')
            except Exception as e:
                print(f'    !! image failed {src}: {e}', file=sys.stderr)
                return ''
        return f'<img src="/assets/blog/{name}" alt="{alt}" loading="lazy" style="max-width:100%;height:auto;border-radius:8px">'

    return IMG_TAG.sub(repl, body)


def clean_body(body, slug):
    body = re.sub(r'<script\b.*?</script>', '', body, flags=re.S | re.I)
    body = re.sub(r'<noscript\b.*?</noscript>', '', body, flags=re.S | re.I)
    body = re.sub(r'</?gen-text[^>]*>', '', body)
    body = localize_images(body, slug)
    # Unwrap squarespace block scaffolding into plain divs (keeps nesting valid).
    body = re.sub(r'\sdata-[a-zA-Z-]+="[^"]*"', '', body)
    body = re.sub(r'\scontenteditable="[^"]*"', '', body)
    return body


PAGE_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="/support.js"></script>
<script src="/anchor-scroll.js" defer></script>
</head>
<body>
<x-dc>
<helmet>
<title>{title} — Paititi Institute Blog</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Paititi Institute">
<meta name="robots" content="noindex">
<meta name="theme-color" content="#2A1736">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/fonts.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/colors.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/typography.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/spacing.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/effects.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/styles.css">
<script src="/_ds/meristem-design-system/_ds_bundle.js"></script>
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<style>
  body{{margin:0;background:var(--surface-page)}}
  a{{color:var(--accent-primary)}}
  .pt-prose{{font-size:17px;line-height:1.75;color:var(--text-body)}}
  .pt-prose h2,.pt-prose h3{{font-family:var(--font-display);color:var(--text-heading);line-height:1.25;margin:1.6em 0 0.5em}}
  .pt-prose h2{{font-size:30px}} .pt-prose h3{{font-size:24px}}
  .pt-prose img{{margin:24px auto;display:block}}
  .pt-prose figure{{margin:24px 0}}
  .pt-prose blockquote{{border-left:3px solid var(--accent-highlight);margin:24px 0;padding:4px 0 4px 20px;color:var(--text-muted)}}
</style>
</helmet>
<div style="font-family:var(--font-body);color:var(--text-body);background:var(--surface-page)">
<dc-import name="SiteHeader" active="blog" style="position:sticky;top:0;z-index:50" hint-size="100%,115px"></dc-import>
<main>
  <article style="max-width:var(--container-narrow);margin:0 auto;padding:64px 24px var(--section-y)">
    <p style="font-size:14px;color:var(--text-muted);margin:0 0 12px">{date} · {author}{cats_line}</p>
    <h1 style="font:var(--text-h1);color:var(--text-heading);margin:0 0 32px">{title}</h1>
    <div class="pt-prose">
{body}
    </div>
    <nav style="display:flex;justify-content:space-between;gap:16px;margin-top:64px;border-top:1px solid var(--border-subtle);padding-top:24px;font-size:15px">
      <span>{prev_link}</span>
      <span>{next_link}</span>
    </nav>
  </article>
  <section style="background:var(--surface-section)">
    <div style="max-width:var(--container);margin:0 auto;padding:56px 24px;text-align:center">
      <a href="/retreats" style="text-decoration:none;font-family:var(--font-display);font-size:24px;font-weight:700;color:var(--text-heading)">Join us for an upcoming retreat →</a>
    </div>
  </section>
</main>
<dc-import name="SiteFooter" hint-size="100%,700px"></dc-import>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props="{{&quot;$preview&quot;:{{&quot;width&quot;:1280,&quot;height&quot;:2400}}}}">
class Component extends DCLogic {{
  renderVals() {{ return {{}}; }}
}}
</script>
</body>
</html>
'''


def cat_name(raw):
    return html_unescape(raw)


def cat_href(name):
    name = cat_name(name)
    slug = CATEGORY_SLUGS.get(name) or re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return '/blog/category/' + slug


def post_page(item, prev_item, next_item):
    slug = slug_of(item)
    date, _ = display_date(item)
    title = html_unescape(item['title']).replace(' ', ' ')
    cats = item.get('categories') or []
    cats_line = ''
    if cats:
        cats_line = ' · ' + ', '.join(
            f'<a href="{cat_href(c)}" style="color:var(--accent-primary);text-decoration:none">{cat_name(c).replace("&", "&amp;")}</a>' for c in cats)
    def link(it, label):
        if not it:
            return ''
        t = html_unescape(it['title']).replace(' ', ' ')
        return f'<a href="/blog/{slug_of(it)}" style="text-decoration:none">{label} {t}</a>'
    body = clean_body(item['body'], slug)
    desc = strip_tags(item.get('excerpt') or '')[:300].replace('"', '&quot;')
    page = PAGE_TEMPLATE.format(
        title=title.replace('"', '&quot;'), description=desc, date=date,
        author=item['author']['displayName'], cats_line=cats_line, body=body,
        prev_link=link(prev_item, '←'), next_link=link(next_item, '→'))
    fname = f'BlogPost-{slug}.dc.html'
    with open(os.path.join(ROOT, fname), 'w') as f:
        f.write(page)
    print(f'  wrote {fname}')
    return slug, fname


def index_card(item, thumb):
    slug = slug_of(item)
    date, _ = display_date(item)
    title = html_unescape(item['title']).replace(' ', ' ')
    excerpt = strip_tags(item.get('excerpt') or '')
    if len(excerpt) > 260:
        excerpt = excerpt[:257].rstrip() + '…'
    is_link_post = bool(item.get('sourceUrl'))
    href = item.get('sourceUrl') or f'/blog/{slug}'
    target = ' target="_blank" rel="noopener"' if is_link_post else ''
    cats = item.get('categories') or []
    cats_html = ''
    if cats:
        cats_html = '<p style="font-size:12px;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;margin:0 0 8px">' + \
            ' '.join(f'<a href="{cat_href(c)}" style="color:var(--accent-primary);text-decoration:none;margin-right:10px">{cat_name(c).replace("&", "&amp;")}</a>' for c in cats) + '</p>'
    excerpt_html = f'<p style="font-size:15px;line-height:1.6;color:var(--text-body);margin:0 0 14px">{excerpt}</p>' if excerpt else ''
    return f'''        <article style="background:var(--surface-card);border:1px solid var(--border-subtle);border-radius:var(--radius-lg);overflow:hidden;display:flex;flex-direction:column">
          <a href="{href}"{target}><img src="/assets/blog/{thumb}" alt="" loading="lazy" style="width:100%;aspect-ratio:3/2;object-fit:cover;display:block"></a>
          <div style="padding:22px 24px 26px;display:flex;flex-direction:column;gap:0;flex:1">
            <p style="font-size:13px;color:var(--text-muted);margin:0 0 10px">{item['author']['displayName']} · {date}</p>
            {cats_html}
            <h2 style="font:var(--text-h3);margin:0 0 10px"><a href="{href}"{target} style="color:var(--text-heading);text-decoration:none">{title}</a></h2>
            {excerpt_html}
            <a href="{href}"{target} style="margin-top:auto;font-weight:700;font-size:14px;text-decoration:none">Read More →</a>
          </div>
        </article>'''


INDEX_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="/support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<title>{page_title} — Paititi Institute</title>
<meta name="description" content="Journal — stories, ancient wisdom and practical guidance from the Paititi Institute.">
<meta property="og:title" content="{page_title} — Paititi Institute">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Paititi Institute">
<meta name="robots" content="noindex">
<meta name="theme-color" content="#2A1736">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/fonts.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/colors.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/typography.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/spacing.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/tokens/effects.css">
<link rel="stylesheet" href="/_ds/meristem-design-system/styles.css">
<script src="/_ds/meristem-design-system/_ds_bundle.js"></script>
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
<style>body{{margin:0;background:var(--surface-page)}} a{{color:var(--accent-primary)}}</style>
</helmet>
<div style="font-family:var(--font-body);color:var(--text-body);background:var(--surface-page)">
<dc-import name="SiteHeader" active="blog" style="position:sticky;top:0;z-index:50" hint-size="100%,115px"></dc-import>
<main>
  <section style="background:var(--surface-page)">
    <div style="max-width:var(--container-wide);margin:0 auto;padding:64px 24px var(--section-y)">
      <h1 class="ink-rule" style="font:var(--text-h1);color:var(--text-heading);margin:0 0 16px">Journal</h1>
      {filter_note}
      <nav aria-label="Categories" style="display:flex;gap:16px;flex-wrap:wrap;margin:24px 0 16px;font-size:14px;font-weight:700">
        <a href="/blog" style="text-decoration:none">All</a>
        <a href="/blog/category/transformation" style="text-decoration:none">Transformation</a>
        <a href="/blog/category/plant-medicine" style="text-decoration:none">Plant Medicine</a>
        <a href="/blog/category/health-wellness" style="text-decoration:none">Health &amp; Wellness</a>
        <a href="/blog/category/indigenous-traditions" style="text-decoration:none">Indigenous Traditions</a>
      </nav>
      <p style="font-size:15px;color:var(--text-muted);margin:0 0 40px">Look for more articles on <a href="https://substack.com/@romanhanis" target="_blank" rel="noopener">Roman's Substack page</a>.</p>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(min(380px,100%),1fr));gap:32px">
{cards}
      </div>
    </div>
  </section>
</main>
<dc-import name="SiteFooter" hint-size="100%,700px"></dc-import>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props="{{&quot;$preview&quot;:{{&quot;width&quot;:1280,&quot;height&quot;:2200}}}}">
class Component extends DCLogic {{
  renderVals() {{ return {{}}; }}
}}
</script>
</body>
</html>
'''


def main():
    print('Fetching blog index JSON…')
    data = fetch_json(f'{SITE}/blog')
    items = sorted(data['items'], key=lambda i: i['publishOn'], reverse=True)
    print(f'{len(items)} posts')

    os.makedirs(ASSET_DIR, exist_ok=True)
    thumbs = {}
    for item in items:
        slug = slug_of(item)
        thumb = f'thumb-{slug}.jpg'
        path = os.path.join(ASSET_DIR, thumb)
        if not os.path.exists(path):
            try:
                with open(path, 'wb') as f:
                    f.write(fetch(item['assetUrl'].split('?')[0] + '?format=800w'))
                print(f'  thumb {thumb}')
            except Exception as e:
                print(f'  !! thumb failed {slug}: {e}', file=sys.stderr)
        thumbs[slug] = thumb

    redirects, sitemap = [], []
    # Post pages (skip external link-posts; they redirect to their source).
    posts = [i for i in items if not i.get('sourceUrl')]
    for idx, item in enumerate(posts):
        print(f'Post: {item["title"][:60]}')
        prev_item = posts[idx + 1] if idx + 1 < len(posts) else None  # older
        next_item = posts[idx - 1] if idx > 0 else None               # newer
        slug, fname = post_page(item, prev_item, next_item)
        redirects.append(f'/blog/{slug} /{fname} 200')
        sitemap.append(f'{SITE}/blog/{slug}')
    for item in items:
        if item.get('sourceUrl'):
            redirects.append(f'/blog/{slug_of(item)} {item["sourceUrl"]} 302')

    # Index + category pages.
    all_cards = '\n'.join(index_card(i, thumbs[slug_of(i)]) for i in items)
    with open(os.path.join(ROOT, 'Blog.dc.html'), 'w') as f:
        f.write(INDEX_TEMPLATE.format(page_title='Blog', filter_note='', cards=all_cards))
    print('  wrote Blog.dc.html')
    redirects.append('/blog /Blog.dc.html 200')

    for name, cslug in CATEGORY_SLUGS.items():
        cat_items = [i for i in items if name in [cat_name(c) for c in (i.get('categories') or [])]]
        cards = '\n'.join(index_card(i, thumbs[slug_of(i)]) for i in cat_items)
        note = f'<p style="font-size:16px;color:var(--text-muted);margin:0">Category: <strong>{name}</strong></p>'
        fname = f'BlogCategory-{cslug}.dc.html'
        with open(os.path.join(ROOT, fname), 'w') as f:
            f.write(INDEX_TEMPLATE.format(page_title=name, filter_note=note, cards=cards))
        print(f'  wrote {fname} ({len(cat_items)} posts)')
        redirects.append(f'/blog/category/{cslug} /{fname} 200')

    print('\n--- add to _redirects ---')
    print('\n'.join(redirects))
    print('\n--- add to sitemap.xml ---')
    print('\n'.join(sitemap))


if __name__ == '__main__':
    main()
