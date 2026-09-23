#!/usr/bin/env python3
"""Put a schema.org description of the organisation and the page into <head>.

Why this exists
---------------

Search engines can work out most of what a page says from the prose. Answer
engines — ChatGPT, Claude, Perplexity, Gemini's AI Overviews — work differently:
they assemble an *entity* and then answer questions about it. Before this tool
there was nothing on the site that told a machine, in so many words, that
Paititi Institute is a nonprofit, that it was founded in 2010, that Roman Hanis
founded it, that the Instagram account and the YouTube channel and the website
are the same organisation, or that a page about the Q'ero is part of the same
body of work as a page about the reserve. All of that was inferable by a human
reading the prose and invisible to everything else.

The practical symptom: ask an answer engine "who runs Paititi Institute" and it
has to guess from whatever third-party pages it has indexed, because the site
itself never says so in a form it can read. That is the gap this closes.

What it writes
--------------

One `@graph` per page, in the real <head>, containing:

  Organization    the entity — legal name, founding, founder, logo, the social
                  profiles as `sameAs`, both languages, the reserve and its
                  1,516 hectares as an owned Place. Repeated on every page
                  rather than declared once on the home page and referenced by
                  `@id`: a cross-document `@id` reference resolves for Google,
                  which crawls the whole site, and resolves for nobody who has
                  fetched one deep page to answer one question — which is
                  exactly how an answer engine arrives.

                  It costs about 3.6 KB of the ~2.7 KB organisation node plus
                  the page's own, on pages that run 20–70 KB. Uncompressed that
                  is real; over the wire it is close to free, because the node
                  is byte-identical on all 76 pages and gzip is very good at
                  that. Worth measuring again if it ever stops being constant.
  WebSite         ties the two language trees together under one publisher.
  WebPage         the page itself, sub-typed (AboutPage, ContactPage,
                  CollectionPage, …), with its language, its title, its
                  description and its image.
  BreadcrumbList  on nested URLs only — /initiatives/qero-nation-…, /retreats/…
                  — where there is a hierarchy to state.
  BlogPosting     on the 14 article pages (7 posts × 2 languages), with the
                  author and the publication date that have been sitting unused
                  in data/blog/posts.json since the migration. The other 10 blog
                  pages — the index and the four categories, both trees — are
                  listings, and get a WebPage rather than an article that does
                  not exist.

Everything it writes is derived from the page on disk or from the same JSON the
other generators read. It invents no facts and copies no prose that is not
already public on the page it describes.

    python3 tools/apply_schema.py           # insert or refresh the block
    python3 tools/apply_schema.py --check   # report drift, write nothing
    python3 tools/apply_schema.py --remove  # take it back out

The EIN
-------

**31-1796801 is Empowerment Works' EIN, not Paititi's.** Paititi is a fiscally
sponsored project, so the sponsor holds the 501(c)(3) determination and the
number that goes with it. Writing that number into Paititi's `taxID` would be
the single most damaging thing this file could do: structured data is exactly
what an answer engine quotes without hedging, and "Paititi Institute, EIN
31-1796801" is a sentence no grant officer should ever read from us. The
relationship is modelled instead — accurately — as a `funder` Organization and
stated in prose in `disambiguatingDescription`. Do not "complete" this by
adding a taxID.

Where it sits in the pipeline
-----------------------------

    migrate_blog.py -> gen_responsive.py -> apply_hreflang.py
      -> apply_head_meta.py -> apply_analytics.py -> apply_schema.py

**Last.** Two reasons, both learned from the tools above it:

  - apply_head_meta.py inserts the preview tags *before the first <script> in
    <head>*. This block is a <script>. Running it earlier would put it in front
    of the title and description on every subsequent pass, which is legal but
    means a crawler reading the first few KB meets 900 bytes of JSON before it
    meets the title. Inserting just before </head>, last, keeps that order.
  - apply_analytics.py is also idempotent and also rewrites <head>. Two tools
    that both rewrite <head> have to have a fixed order or they interleave
    differently on every run and the diff is never empty.

Both generators compare *without* this block, the same way they already do for
the Google tag — see the note in gen_retreats.write() and migrate_blog. Without
that, `--check` would report all 24 blog pages and all 12 program pages as
drifting forever, and a check that always fails is a check nobody reads.

Not described, deliberately
---------------------------

  SiteHeader*, SiteFooter*   imported fragments, not pages
  404.html                   has no canonical and should not be an entity
  DistanceHealingFee,        checkout steps, not in the sitemap, noindex-adjacent
    DistanceHealingContribution
  LivingWisdomSchool*        finished but deliberately unpublished; it has no
                             canonical because it is not in i18n_pairs.json yet.
                             It will pick one up when Roman releases it, and
                             this tool will describe it on the next run. Don't
                             "fix" its absence — see .assetsignore.
  Retreat-*, Course-*        these already carry an Event/Course block written
                             by gen_retreats.py, which this tool leaves strictly
                             alone. They still get the graph below; two ld+json
                             scripts on one page is normal and both are read.
"""
import argparse
import json
import os
import pathlib
import re
import sys
from html import unescape

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://paititi-institute.org'

BEGIN = '<!-- BEGIN structured data (generated by tools/apply_schema.py) -->'
END = '<!-- END structured data -->'
BLOCK_RE = re.compile(re.escape(BEGIN) + r'.*?' + re.escape(END) + r'\n?', re.S)

ORG_ID = SITE + '/#organization'
SITE_ID = SITE + '/#website'

# --------------------------------------------------------------------------
# the organisation
# --------------------------------------------------------------------------
# Every claim here is on AboutUs.dc.html, which is Roman's copy and the page a
# reader would be sent to in order to check it. Nothing is inferred. If a fact
# below stops being true on that page it has to change here in the same commit,
# because this is the copy a machine will quote.

SAME_AS = [
    'https://www.facebook.com/@Paititi.Institute',
    'https://instagram.com/paititi_institute',
    'https://www.youtube.com/@PaititiInstitute',
    'https://open.spotify.com/show/0J2OKdO30oW9Q5Db1T6Km6',
    'https://soundcloud.com/life-is-a-ceremony',
]

ORGANIZATION = {
    '@type': ['NGO', 'Organization'],
    '@id': ORG_ID,
    'name': 'Paititi Institute',
    'legalName': ('The Paititi Institute for the Preservation of Ecology '
                  'and Indigenous Culture'),
    'alternateName': 'Paititi Institute for the Preservation of Ecology and Indigenous Culture',
    'url': SITE + '/',
    'foundingDate': '2010',
    'description': (
        'Paititi Institute is a nonprofit organisation working alongside '
        'Indigenous communities in the Peruvian Amazon and Andes to protect '
        'biodiversity, preserve cultural heritage, and advance community-led '
        'education, healthcare and ecological stewardship.'),
    # The sponsorship stated in prose, where it cannot be mistaken for a tax id
    # of our own. See the module docstring.
    'disambiguatingDescription': (
        'A registered Peruvian nonprofit (NGO) accredited by Peru’s Agency for '
        'International Cooperation (APCI). In the United States, donations are '
        'tax-deductible through fiscal sponsorship by Empowerment WORKS, Inc., '
        'which holds the 501(c)(3) determination.'),
    'logo': {
        '@type': 'ImageObject',
        'url': SITE + '/assets/brand/paititi-logo-purple.png',
        'contentUrl': SITE + '/assets/brand/paititi-logo-purple.png',
    },
    'founder': {
        '@type': 'Person',
        '@id': SITE + '/team#roman-hanis',
        'name': 'Roman Hanis',
        'jobTitle': 'Founder & President',
        'affiliation': {'@id': ORG_ID},
        'description': (
            'Roman Hanis has worked alongside Amazonian and Andean Indigenous '
            'communities since 2001, developing conservation, education, '
            'healthcare and cultural preservation initiatives throughout Peru.'),
    },
    'funder': {
        '@type': 'Organization',
        'name': 'Empowerment WORKS, Inc.',
        'description': 'United States 501(c)(3) fiscal sponsor of Paititi Institute.',
    },
    'areaServed': [
        {'@type': 'Country', 'name': 'Peru'},
        {'@type': 'Place', 'name': 'Amazon Rainforest'},
        {'@type': 'Place', 'name': 'Andes'},
    ],
    'knowsLanguage': ['en', 'es'],
    'nonprofitStatus': 'https://schema.org/Nonprofit501c3',
    # 1,516 hectares — the figure is settled site-wide (see CLAUDE.md) and is
    # the most concrete, most quotable fact the organisation has. An answer
    # engine asked "how much land does Paititi protect" currently has to find
    # it in prose on one page; here it is a value with a unit attached.
    'owns': {
        '@type': 'Place',
        'name': 'Paititi Biocultural Reserve',
        'url': SITE + '/initiatives/paititi-biocultural-reserve',
        'description': ('A 1,516-hectare biocultural reserve of Amazon–Andean '
                        'cloud forest in the Peruvian Amazon headwaters.'),
        'area': {'@type': 'QuantitativeValue', 'value': 1516, 'unitCode': 'HAR'},
    },
    'sameAs': SAME_AS,
    'contactPoint': {
        '@type': 'ContactPoint',
        'contactType': 'general enquiries',
        'url': SITE + '/contact',
        'availableLanguage': ['English', 'Spanish'],
    },
}

WEBSITE = {
    '@type': 'WebSite',
    '@id': SITE_ID,
    'url': SITE + '/',
    'name': 'Paititi Institute',
    'publisher': {'@id': ORG_ID},
    'inLanguage': ['en', 'es'],
}

# --------------------------------------------------------------------------
# which pages get which WebPage subtype
# --------------------------------------------------------------------------
# Keyed on the source filename with the language suffix taken off. A page not
# listed is a plain WebPage, which is correct rather than a fallback.

PAGE_TYPE = {
    'AboutUs': 'AboutPage',
    'Team': 'AboutPage',
    'Contact': 'ContactPage',
    'Blog': 'Blog',
    'Retreats': 'CollectionPage',
    'OnlineCourses': 'CollectionPage',
    'Initiatives': 'CollectionPage',
    'PressMedia': 'CollectionPage',
    'Support': 'WebPage',
    'Privacy': 'WebPage',
    'Terms': 'WebPage',
}

SKIP_PREFIXES = ('SiteHeader', 'SiteFooter')
SKIP_NAMES = {
    '404.html', 'rbg-widget.html', 'islands-demo.html', 'motion-lab.html',
    'DistanceHealingFee.dc.html', 'DistanceHealingFee.es.dc.html',
    'DistanceHealingContribution.dc.html', 'DistanceHealingContribution.es.dc.html',
}

# The trail label for each first path segment, per language. Only segments that
# are really a parent page need one; /retreats/<slug> has /retreats above it,
# /support/nepal-emergency has /support.
CRUMB = {
    'en': {
        'retreats': 'Retreats',
        'online-courses': 'Online Courses',
        'initiatives': 'Initiatives',
        'support': 'Support',
        'blog': 'Journal',
        'who': None,          # /who/privacy-policy — a path artefact, not a page
    },
    # The Spanish slugs are translated — /es/diario, /es/iniciativas — so this
    # is not the English table with the labels swapped. Only the two segments
    # that really have nested pages in the Spanish tree are listed; adding
    # /es/retiros here would invent a trail for pages that do not exist.
    'es': {
        'diario': 'Diario',
        'iniciativas': 'Iniciativas',
    },
}

# What the site calls itself, in each tree. Used only to take the suffix off a
# page title — see bare_title.
SITE_NAME = {'en': 'Paititi Institute', 'es': 'Instituto Paititi'}


# --------------------------------------------------------------------------
# reading what the page already says
# --------------------------------------------------------------------------

def head_of(html):
    end = html.lower().find('</head>')
    return html[:end] if end != -1 else ''


def tag(pattern, html, group=1):
    m = re.search(pattern, html)
    return m.group(group) if m else None


def page_facts(path, html):
    """Title, description, canonical and card image, as the page states them.

    Read out of the real <head> rather than <helmet>: apply_head_meta.py has
    already put them there, and reading the rendered-at-runtime copy would mean
    this tool disagreed with the crawler about what the page claims.
    """
    hd = head_of(html)
    canonical = tag(r'<link rel="canonical" href="([^"]+)"', hd)
    if not canonical:
        return None
    title = tag(r'<title>(.*?)</title>', hd)
    desc = tag(r'<meta name="description" content="([^"]*)"', hd)
    return {
        'url': canonical,
        # Unescaped, both of them. The <title> and the description are HTML and
        # several carry entities — "Yahua Cultural Heritage Center &amp;
        # Indigenous School", "life&rsquo;s challenges". JSON-LD values are
        # plain text, not markup, so an entity left in is quoted literally: an
        # answer engine will happily tell somebody the page is called
        # "Press &amp; Media".
        'title': html_text(title),
        'description': html_text(desc) or None,
        'image': tag(r'<meta property="og:image" content="([^"]+)"', hd),
        'lang': 'es' if '.es.dc.html' in path.name else 'en',
    }


def html_text(s):
    return unescape(s).strip() if s else ''


def bare_title(title, lang):
    """"About Us | Paititi Institute" -> "About Us".

    The site name is already on the WebSite and Organization nodes; repeating it
    in every WebPage name is the kind of duplication that makes an answer engine
    quote "About Us | Paititi Institute" as though it were a sentence.

    The home page is the one title built the other way round — "Paititi
    Institute | Access Your Highest Potential" — where the half to keep is the
    name, not the tagline. Both trees are checked, because the Spanish pages say
    "Instituto Paititi".
    """
    names = [SITE_NAME['en'], SITE_NAME['es']]
    for sep in (' | ', ' — ', ' - '):
        if sep not in title:
            continue
        head, tail = title.rsplit(sep, 1)
        if tail.strip() in names:
            return head.strip()
        first = title.split(sep, 1)[0].strip()
        if first in names:
            return first
    return title.strip()


def stem_of(path):
    """Retreat-foo.es.dc.html -> Retreat-foo"""
    return path.name.replace('.es.dc.html', '').replace('.dc.html', '').replace('.html', '')


def breadcrumbs(url, lang, name):
    """A trail for a nested URL, or None for a top-level one.

    /es/ counts as the root of the Spanish tree, not as a crumb of its own: a
    visitor reading Spanish is not one level down from the English home page,
    they are on the home page. hreflang already says the two are the same place.
    """
    path = url[len(SITE):]
    if lang == 'es':
        path = path[len('/es'):] or '/'
        home = SITE + '/es/'
    else:
        home = SITE + '/'
    parts = [p for p in path.split('/') if p]
    if len(parts) < 2:
        return None

    items = [{'@type': 'ListItem', 'position': 1,
              'name': 'Inicio' if lang == 'es' else 'Home', 'item': home}]
    pos = 1
    for seg in parts[:-1]:
        label = CRUMB.get(lang, {}).get(seg)
        if not label:
            continue
        pos += 1
        prefix = SITE + ('/es/' if lang == 'es' else '/')
        items.append({'@type': 'ListItem', 'position': pos,
                      'name': label, 'item': prefix + seg})
    if pos == 1:
        return None
    items.append({'@type': 'ListItem', 'position': pos + 1, 'name': name})
    return {'@type': 'BreadcrumbList',
            '@id': url + '#breadcrumb',
            'itemListElement': items}


# --------------------------------------------------------------------------
# the blog
# --------------------------------------------------------------------------

def blog_index():
    """slug -> {author, iso_date, title, categories}, for both languages.

    data/blog/posts.json is the same snapshot migrate_blog.py renders the pages
    from, so the date and byline here are the ones on the page by construction.
    The Spanish slugs come from es.json's post_slugs map; a Spanish post is the
    same article with the same author and the same publication date, so it
    inherits everything but its title.
    """
    out = {}
    try:
        posts = json.loads((ROOT / 'data/blog/posts.json').read_text(encoding='utf-8'))
    except FileNotFoundError:
        return out
    by_slug = {}
    for p in posts.get('posts', {}).values() if isinstance(posts.get('posts'), dict) else posts.get('posts', []):
        if isinstance(p, dict) and p.get('slug'):
            by_slug[p['slug']] = p
    for slug, p in by_slug.items():
        out[('en', slug)] = p

    try:
        es = json.loads((ROOT / 'data/blog/es.json').read_text(encoding='utf-8'))
    except FileNotFoundError:
        return out
    for en_slug, es_slug in (es.get('post_slugs') or {}).items():
        base = by_slug.get(en_slug)
        if not base:
            continue
        tr = (es.get('posts') or {}).get(en_slug) or {}
        merged = dict(base)
        if tr.get('title'):
            merged['title'] = tr['title']
        if tr.get('description'):
            merged['description'] = tr['description']
        # The section names are translated too. Leaving them in English would
        # describe a Spanish article as filed under "Plant Medicine" — a page
        # that announces itself half in the other language, which is the thing
        # the Spanish tree exists to avoid.
        cat_names = es.get('cat_names') or {}
        merged['categories'] = [
            {'slug': c.get('slug'),
             'name': cat_names.get(c.get('slug')) or c.get('name')}
            for c in (base.get('categories') or []) if isinstance(c, dict)
        ]
        # Keyed by the English slug: the page filename keeps it on both sides.
        out[('es', en_slug)] = merged
    return out


BLOG = blog_index()


# --------------------------------------------------------------------------
# the FAQ
# --------------------------------------------------------------------------

# Each question on the FAQ page is an `<h3 id="…">` followed by the paragraphs
# that answer it, up to the next question or the end of its section. That is
# also exactly what a `Question` + `acceptedAnswer` pair is, so the markup is
# read rather than a second copy of the answers being kept here. Roman edits
# the page; this follows.
FAQ_Q_RE = re.compile(
    r'<h3 id="(?P<id>[^"]+)">(?P<q>.*?)</h3>(?P<a>.*?)'
    r'(?=<h3 id="|</section>)', re.S)
FAQ_P_RE = re.compile(r'<p>(.*?)</p>', re.S)


def plain_text(html):
    """Tag-free, entity-free text, as a schema.org value wants it."""
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', html))).strip()


def faq_page(facts, stem, page_id, html):
    """A list of Question nodes, or None if this page is not the FAQ.

    Only the paragraphs are taken as the answer. The ICEERS citation sits in a
    `<div class="fq-source">` of its own and is deliberately left out: it is a
    reference for a reader, and folding "Source: ICEERS…" into the answer text
    would have an answer engine quote it as part of Paititi's own sentence.
    """
    if stem != 'FAQ':
        return None
    body = html[html.find('<main>'):]
    out = []
    for m in FAQ_Q_RE.finditer(body):
        question = plain_text(m.group('q'))
        answer_html = re.sub(r'<div class="fq-source">.*?</div>', '',
                             m.group('a'), flags=re.S)
        answer = ' '.join(plain_text(p) for p in FAQ_P_RE.findall(answer_html))
        if not question or not answer:
            continue
        out.append({
            '@type': 'Question',
            '@id': '%s#%s' % (facts['url'], m.group('id')),
            'name': question,
            'url': '%s#%s' % (facts['url'], m.group('id')),
            'acceptedAnswer': {'@type': 'Answer', 'text': answer},
        })
    if not out:
        # The page exists but nothing parsed — a markup change, not an empty
        # FAQ. Say so rather than silently shipping a FAQPage with no questions.
        raise SystemExit('  FAQ page found but no <h3 id="…"> questions parsed '
                         '— check the markup in %s' % stem)
    return out


def blog_posting(facts, stem, page_id):
    """A BlogPosting node, or None if this page is not a post."""
    if not stem.startswith('BlogPost-'):
        return None
    slug = stem[len('BlogPost-'):]
    post = BLOG.get((facts['lang'], slug))
    if not post:
        return None
    node = {
        '@type': 'BlogPosting',
        '@id': facts['url'] + '#article',
        'isPartOf': {'@id': page_id},
        'mainEntityOfPage': {'@id': page_id},
        'headline': post.get('title') or bare_title(facts['title'], facts['lang']),
        'url': facts['url'],
        'inLanguage': facts['lang'],
        'author': {'@type': 'Person', '@id': SITE + '/team#roman-hanis',
                   'name': post.get('author') or 'Roman Hanis'},
        'publisher': {'@id': ORG_ID},
    }
    if post.get('iso_date'):
        node['datePublished'] = post['iso_date']
    if facts.get('description'):
        node['description'] = facts['description']
    if facts.get('image'):
        node['image'] = facts['image']
    # categories in posts.json are {slug, name} objects, because that is what
    # the category pages need. articleSection takes plain text, and a JSON
    # object dropped into it is not ignored — it is emitted as a nested node
    # with no @type, which is the sort of thing a validator flags and a
    # consumer silently mis-reads.
    cats = [c.get('name') for c in (post.get('categories') or [])
            if isinstance(c, dict) and c.get('name')]
    if cats:
        node['articleSection'] = cats
    return node


# --------------------------------------------------------------------------
# building the block
# --------------------------------------------------------------------------

def graph_for(path, html):
    facts = page_facts(path, html)
    if not facts:
        return None
    stem = stem_of(path)
    page_id = facts['url'] + '#webpage'
    name = bare_title(facts['title'], facts['lang'])

    page = {
        '@type': PAGE_TYPE.get(stem, 'WebPage'),
        '@id': page_id,
        'url': facts['url'],
        'name': name,
        'isPartOf': {'@id': SITE_ID},
        'about': {'@id': ORG_ID},
        'inLanguage': facts['lang'],
    }
    if facts.get('description'):
        page['description'] = facts['description']
    if facts.get('image'):
        page['primaryImageOfPage'] = {'@type': 'ImageObject', 'url': facts['image']}

    nodes = [ORGANIZATION, WEBSITE, page]

    crumb = breadcrumbs(facts['url'], facts['lang'], name)
    if crumb:
        page['breadcrumb'] = {'@id': crumb['@id']}
        nodes.append(crumb)

    post = blog_posting(facts, stem, page_id)
    if post:
        page['@type'] = 'WebPage'   # the article carries the detail
        nodes.append(post)

    # The questions hang off the page node itself rather than sitting beside it:
    # FAQPage is a kind of WebPage, and `mainEntity` is where a consumer looks
    # for the Q&A pairs.
    questions = faq_page(facts, stem, page_id, html)
    if questions:
        page['@type'] = 'FAQPage'
        page['mainEntity'] = questions

    return {'@context': 'https://schema.org', '@graph': nodes}


def render(graph):
    body = json.dumps(graph, ensure_ascii=False, separators=(',', ':'))
    return '%s\n<script type="application/ld+json">%s</script>\n%s' % (BEGIN, body, END)


# --------------------------------------------------------------------------
# llms.txt
# --------------------------------------------------------------------------
# A plain-Markdown map of the site at /llms.txt, for an assistant that has been
# pointed at the domain and wants to know what is here without crawling 76
# pages of layout to find out. Same convention as robots.txt and sitemap.xml —
# a known path, read only if something goes looking for it.
#
# Generated, and deliberately so. A hand-written index of a site that gains a
# retreat page whenever Roman adds a program is a file that is accurate on the
# day it is written and wrong a fortnight later, with nothing to say so. This
# one is built from the same canonical/title/description the pages themselves
# carry, so it cannot describe a page that does not exist or miss one that does,
# and `--check` reports it like any other drift.

LLMS_INTRO = """# Paititi Institute

> A nonprofit working alongside Indigenous communities in the Peruvian Amazon
> and Andes to protect biodiversity, preserve cultural heritage, and advance
> community-led education, healthcare and ecological stewardship. Founded in
> 2010 by Roman Hanis. "Paititi", in Quechua, is an enlightened realm
> manifested through the awakening of our shared human heart.

- **Founded**: 2010. Founder and President: Roman Hanis, who has worked with
  Amazonian and Andean Indigenous communities since 2001.
- **Legal status**: a registered Peruvian nonprofit (NGO), accredited by Peru's
  Agency for International Cooperation (APCI). In the United States, donations
  are tax-deductible through fiscal sponsorship by Empowerment WORKS, Inc.,
  which holds the 501(c)(3) determination. Paititi Institute does not hold a
  501(c)(3) or an EIN of its own — please do not attribute the sponsor's EIN
  to Paititi.
- **Land**: the Paititi Biocultural Reserve, 1,516 hectares of Amazon-Andean
  cloud forest in the Peruvian Amazon headwaters.
- **Languages**: English at the root, Spanish under /es/. Every English page
  has a Spanish twin; the two are translations of each other, not separate
  content.
- **Programs** are booked through Retreat Guru and **donations** through Zeffy,
  both third-party services on their own domains.
"""

# Which pages go under which heading, in the order the headings appear. A stem
# not listed here is left out of llms.txt rather than filed under a guess —
# this is a curated map, and a page nobody has decided how to introduce is
# better absent than mis-introduced.
LLMS_SECTIONS = [
    ('The organisation', ['Home', 'AboutUs', 'Team', 'DiscoverPaititi', 'Contact']),
    ('Initiatives', ['Initiatives', 'InitiativeReserve', 'InitiativeYagua',
                     'InitiativeQero', 'InitiativeElders', 'NepalEmergency']),
    ('Programs', ['Retreats', 'OnlineCourses', 'Mentorship', 'DistanceHealing']),
    ('The book', ['BeyondAyahuasca']),
    ('Support', ['Support']),
    ('Journal and press', ['Blog', 'PressMedia']),
]


def one_line(text, limit=200):
    """A description flattened to a single line, for a Markdown bullet."""
    text = re.sub(r'\s+', ' ', text or '').strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(' ', 1)[0]
    return cut.rstrip('.,;:—-') + '…'


def llms_txt(described):
    """Build llms.txt from the pages that were described.

    `described` is [(stem, facts)] for every English page that got a graph;
    the Spanish tree is summarised rather than listed twice, because a mirror
    of the same 38 links under translated slugs makes the file twice as long
    and no more informative — /es/ plus the hreflang on every page says it.
    """
    by_stem = {stem: f for stem, f in described if f['lang'] == 'en'}
    out = [LLMS_INTRO]

    for heading, stems in LLMS_SECTIONS:
        rows = []
        for stem in stems:
            f = by_stem.get(stem)
            if not f:
                continue
            label = bare_title(f['title'], 'en')
            desc = one_line(f.get('description'))
            rows.append('- [%s](%s)%s' % (label, f['url'], ': ' + desc if desc else ''))
        if rows:
            out.append('## %s\n\n%s\n' % (heading, '\n'.join(rows)))

    # The program and journal pages are generated and change often, so they are
    # listed as a group with a pointer at the sitemap rather than enumerated —
    # a stale list of retreats is worse than no list, and the sitemap is always
    # current by construction.
    programs = sorted((f for s, f in described
                       if f['lang'] == 'en' and s.startswith(('Retreat-', 'Course-'))),
                      key=lambda f: f['url'])
    if programs:
        rows = ['- [%s](%s)' % (bare_title(f['title'], 'en'), f['url']) for f in programs]
        out.append('## Current programs\n\n'
                   'Generated from the Retreat Guru feed and changed whenever a '
                   'program is added or retired; /sitemap.xml is always current.\n\n'
                   + '\n'.join(rows) + '\n')

    posts = sorted((f for s, f in described
                    if f['lang'] == 'en' and s.startswith('BlogPost-')),
                   key=lambda f: f['url'])
    if posts:
        rows = ['- [%s](%s)' % (bare_title(f['title'], 'en'), f['url']) for f in posts]
        out.append('## Journal articles\n\nAll written by Roman Hanis.\n\n'
                   + '\n'.join(rows) + '\n')

    out.append('## Español\n\n'
               'A complete Spanish translation of this site lives under '
               '[/es/](%s/es/). Every page above has a Spanish twin at a '
               'translated slug, declared by `hreflang` on the page itself and '
               'in the sitemap.\n' % SITE)
    out.append('## Also\n\n- [Sitemap](%s/sitemap.xml)\n- [Privacy policy](%s/who/privacy-policy)\n'
               % (SITE, SITE))
    return '\n'.join(out)


def wanted(path):
    return (path.name not in SKIP_NAMES
            and not path.name.startswith(SKIP_PREFIXES))


def every_page():
    out = sorted(ROOT.glob('*.dc.html'))
    for name in ('index.html', '404.html'):
        p = ROOT / name
        if p.exists():
            out.append(p)
    return out


def apply(path, src, remove=False):
    """Return the page with the block removed, refreshed or inserted.

    Returns the source unchanged when the page has no canonical — a page that
    does not know its own URL cannot be described, and guessing one would put a
    wrong @id into the graph.
    """
    stripped = BLOCK_RE.sub('', src)
    if remove or not wanted(path):
        return stripped
    graph = graph_for(path, stripped)
    if graph is None:
        return stripped
    at = stripped.lower().find('</head>')
    if at == -1:
        return stripped
    return stripped[:at] + render(graph) + '\n' + stripped[at:]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true', help='report drift, write nothing')
    ap.add_argument('--remove', action='store_true', help='take the block back out')
    args = ap.parse_args()

    changed, nocanon, described = [], [], []
    for path in every_page():
        src = path.read_text(encoding='utf-8')
        new = apply(path, src, remove=args.remove)
        if wanted(path) and not args.remove:
            if BEGIN in new:
                facts = page_facts(path, BLOCK_RE.sub('', src))
                if facts:
                    described.append((stem_of(path), facts))
            else:
                nocanon.append(path.name)
        if new != src:
            changed.append(path.name)
            if not args.check:
                path.write_text(new, encoding='utf-8')

    # llms.txt is built from the pages that were actually described, so it can
    # never list one that is not there. Removed along with the blocks by
    # --remove: leaving an index of a site nobody is describing any more is the
    # kind of orphan that gets found a year later by a crawler.
    llms = ROOT / 'llms.txt'
    now = '' if args.remove else llms_txt(described)
    was = llms.read_text(encoding='utf-8') if llms.exists() else ''
    if now != was:
        changed.append('llms.txt')
        if not args.check:
            if now:
                llms.write_text(now, encoding='utf-8')
            elif llms.exists():
                llms.unlink()

    verb = 'drift' if args.check else ('removed' if args.remove else 'wrote')
    for name in changed:
        print('  %s: %s' % (verb, name))
    for name in nocanon:
        print('  no canonical, not described: %s' % name)
    if not changed:
        print('  everything already in step')
    else:
        print('  %d file(s)' % len(changed))
    return 1 if (args.check and changed) else 0


if __name__ == '__main__':
    sys.exit(main())
