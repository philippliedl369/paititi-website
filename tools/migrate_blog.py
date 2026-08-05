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
    """The site shows M/D/YY; the ISO form goes into <time datetime>."""
    dt = datetime.fromtimestamp(item['publishOn'] / 1000, tz=SITE_TZ)
    return f'{dt.month}/{dt.day}/{dt.strftime("%y")}', dt.strftime('%Y-%m-%d')


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
        return f'<img src="/assets/blog/{name}" alt="{alt}" loading="lazy" style="max-width:100%;height:auto">'

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
<link rel="icon" href="/favicon.ico" sizes="any">
<script src="/support.js"></script>
<script src="/anchor-scroll.js" defer></script>
</head>
<body>
<x-dc>
<helmet>
<title>{title} | Paititi Institute</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title} | Paititi Institute">
<meta property="og:description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Paititi Institute">
<meta property="article:published_time" content="{iso_date}">
<meta name="robots" content="noindex">
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
<dc-import name="SiteHeader" active="blog" hint-size="100%,209px"></dc-import>
<main>

  <section class="pt-sec pt-sec-flat bp-sec">
    <div class="pt-sec-bg"></div>
    <article class="bp-item">
      <h1>{title}</h1>
      <p class="bp-meta">{cats_line}<a class="bp-author" href="/team">{author}</a><time datetime="{iso_date}">{date}</time></p>
      <div class="bp-body pt-prose">
{body}
      </div>
    </article>
  </section>

  <nav class="bp-pager" aria-label="More journal entries">
    {prev_link}
    {next_link}
  </nav>

</main>
<dc-import name="SiteFooter"></dc-import>
</div>
</x-dc>
</body>
</html>
'''

# The blog item template, measured off the live post pages: one near-black
# section, a 596px measure centred at x=422, reversed out white throughout.
POST_CSS = """
  .bp-sec{--pt-bg:#210416;color:#fff}
  .bp-item{max-width:596px;margin:0 auto;padding:266px 0 0}
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

  .bp-body{margin-top:87px}
  .bp-body img{max-width:100%;height:auto;display:block}
  /* Squarespace's half-width floated images inside post bodies. */
  .bp-body .float-right{float:right;width:47%;margin:0 0 24px 28px}
  .bp-body .float-left{float:left;width:47%;margin:0 28px 24px 0}
  .bp-body .float-right::after,.bp-body .float-left::after{content:"";display:table;clear:both}
  .bp-body a{color:#fff;text-decoration:underline;text-underline-offset:3px}
  .pt-page .bp-body h2{font-size:41.6px;line-height:1.3104}
  .pt-page .bp-body h3{font-size:28.8px;line-height:1.3552}

  /* Previous / next, two half-width targets on the same dark ground. */
  .bp-pager{display:grid;grid-template-columns:1fr 1fr;gap:0;background:#210416;padding:44px 58px}
  .bp-pager a{display:block;text-decoration:none;color:#fff;max-width:662px}
  .bp-pager .bp-pager-label{display:block;font-size:14.272px;margin-bottom:6px;opacity:.8}
  .pt-page .bp-pager h2{font-family:var(--font-display);font-weight:400;font-size:28.8px;line-height:1.3552;
    color:#fff;margin:0;letter-spacing:normal}
  .bp-pager .bp-next{text-align:left}

  @media (max-width:1180px){
    .bp-item{padding:calc(var(--pt-header-h,209px) + 57px) 24px 0}
    .bp-body .float-right,.bp-body .float-left{float:none;width:100%;margin:0 0 24px}
    .pt-page .bp-sec h1{font-size:40px}
    .pt-page .bp-body h2{font-size:30px}
    .bp-pager{grid-template-columns:1fr;gap:28px;padding:36px 24px}
  }
"""


def cat_name(raw):
    return html_unescape(raw)


def cat_href(name):
    name = cat_name(name)
    slug = CATEGORY_SLUGS.get(name) or re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return '/blog/category/' + slug


def post_page(item, prev_item, next_item):
    slug = slug_of(item)
    date, iso_date = display_date(item)
    title = html_unescape(item['title']).replace('\u00a0', ' ')
    cats = item.get('categories') or []
    # The live byline is a flat run of category links, then author, then date.
    cats_line = ''.join(
        f'<a href="{cat_href(c)}">{cat_name(c).replace("&", "&amp;")}</a>' for c in cats)

    def link(it, label, cls):
        if not it:
            return '<span></span>'
        t = html_unescape(it['title']).replace('\u00a0', ' ')
        return (f'<a class="{cls}" href="/blog/{slug_of(it)}">'
                f'<span class="bp-pager-label">{label}</span><h2>{t}</h2></a>')

    body = clean_body(item['body'], slug)
    desc = strip_tags(item.get('excerpt') or '')[:300].replace('"', '&quot;')
    page = PAGE_TEMPLATE.format(
        title=title.replace('"', '&quot;'), description=desc,
        date=date, iso_date=iso_date, css=POST_CSS.strip(),
        author=item['author']['displayName'], cats_line=cats_line, body=body,
        prev_link=link(prev_item, 'Previous', 'bp-prev'),
        next_link=link(next_item, 'Next', 'bp-next'))
    fname = f'BlogPost-{slug}.dc.html'
    with open(os.path.join(ROOT, fname), 'w') as f:
        f.write(page)
    print(f'  wrote {fname}')
    return slug, fname


def index_card(item, thumb):
    """One card in the 2-up grid: image, 20px spacer, byline, title, excerpt."""
    slug = slug_of(item)
    date, iso_date = display_date(item)
    title = html_unescape(item['title']).replace('\u00a0', ' ')
    # Squarespace prints the excerpt field in full; don't second-guess it.
    excerpt = strip_tags(item.get('excerpt') or '')
    href = item.get('sourceUrl') or f'/blog/{slug}'
    target = ' target="_blank" rel="noopener"' if item.get('sourceUrl') else ''
    excerpt_html = f'<div class="bl-excerpt">{excerpt}</div>'
    return f'''        <article class="bl-card">
          <a class="bl-image" href="{href}"{target}><img src="/assets/blog/{thumb}" alt="" loading="lazy"></a>
          <div class="bl-text">
            <p class="bl-meta"><span>{item['author']['displayName']}</span><time datetime="{iso_date}">{date}</time></p>
            <h2 class="bl-title"><a href="{href}"{target}>{title}</a></h2>
            {excerpt_html}
            <a class="bl-more" href="{href}"{target}>Read More</a>
          </div>
        </article>'''


INDEX_TEMPLATE = '''<!DOCTYPE html>
<html>
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
<title>{page_title} | Paititi Institute</title>
<meta name="description" content="A living space where ancient wisdom meets modern insight to inspire your journey toward personal and planetary transformation.">
<meta property="og:title" content="{page_title} | Paititi Institute">
<meta property="og:description" content="A living space where ancient wisdom meets modern insight to inspire your journey toward personal and planetary transformation.">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Paititi Institute">
<meta property="og:image" content="/assets/blog/69265356-2542807292472488-6841856973810434048-n.webp">
<meta name="robots" content="noindex">
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
<dc-import name="SiteHeader" active="blog" hint-size="100%,209px"></dc-import>
<main>

  <!-- ===== Hero ===== -->
  <section class="pt-sec pt-sec-flat pt-hero bl-hero">
    <div class="pt-sec-bg">
      <img src="/assets/blog/69265356-2542807292472488-6841856973810434048-n.webp" alt="Gathering at the Paititi retreat centre" loading="eager">
    </div>
    <div class="pt-fluid" style="--pt-grid-top:304px;--pt-grid-bot:124px;--pt-rows:16;--pt-row-h:25.8906px">
      <div class="pt-hero-panel pt-prose" style="grid-area:1 / 6 / 10 / 20">
        <h1><strong>Living Transmissions</strong></h1>
        <p>A living space where ancient wisdom meets modern insight to inspire your journey toward personal and planetary transformation. Here, we share stories, reflections, and practical guidance rooted in indigenous traditions, ecological stewardship, and conscious living.</p>
      </div>
      <div class="pt-fit" style="grid-area:9 / 10 / 15 / 16">
        <img src="/assets/brand/icon-vision-purpose.webp" alt="Stylized Buddha eyes over water with lotus petals" loading="eager">
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
        <p><strong>Look for more articles with Romans Substack page </strong><a href="https://substack.com/@romanhanis?utm_source=global-search" target="_blank" rel="noopener"><strong>HERE</strong></a></p>
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
<dc-import name="SiteFooter"></dc-import>
</div>
</x-dc>
</body>
</html>
'''

# The index and the four category pages share one template. Measured off the
# live /blog: a 2-up grid of 512px cards inside the 1200px column, 57.6px
# padding, 60px column gap and 65px row gap, reversed out on near-black.
INDEX_CSS = '''
  .bl-hero{--pt-hero-h:1006px;--pt-bg:#210416;--pt-scrim:rgba(33,4,22,.49)}
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
        f.write(INDEX_TEMPLATE.format(page_title='Journal', filter_note='',
                                      css=INDEX_CSS.strip(), cards=all_cards))
    print('  wrote Blog.dc.html')
    redirects.append('/blog /Blog.dc.html 200')

    for name, cslug in CATEGORY_SLUGS.items():
        cat_items = [i for i in items if name in [cat_name(c) for c in (i.get('categories') or [])]]
        cards = '\n'.join(index_card(i, thumbs[slug_of(i)]) for i in cat_items)
        # The live category pages show the filtered grid and nothing else —
        # no "showing X" banner — so don't invent one.
        note = ''
        fname = f'BlogCategory-{cslug}.dc.html'
        with open(os.path.join(ROOT, fname), 'w') as f:
            f.write(INDEX_TEMPLATE.format(page_title=name + ' \u2014 Journal', filter_note=note,
                                          css=INDEX_CSS.strip(), cards=cards))
        print(f'  wrote {fname} ({len(cat_items)} posts)')
        redirects.append(f'/blog/category/{cslug} /{fname} 200')

    print('\n--- add to _redirects ---')
    print('\n'.join(redirects))
    print('\n--- add to sitemap.xml ---')
    print('\n'.join(sitemap))


if __name__ == '__main__':
    main()
