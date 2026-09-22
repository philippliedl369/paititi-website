# SEO setup — template

The skeleton ships with `noindex` on every page and `example.com` as the
domain placeholder. Before launch:

1. **Domain** — find-and-replace `example.com` across the repo (canonical URLs,
   OG tags, `robots.txt`, `sitemap.xml`).
2. **Unblock indexing** — remove `<meta name="robots" content="noindex">` from
   pages that should rank; keep it on utility pages (demos, fragments).
   `SiteHeader.dc.html`/`SiteFooter.dc.html` stay noindexed via `_headers`.
3. **Per-page meta** — unique `<title>` (~55 chars) and `<meta name="description">`
   (~155 chars) in each page's `<helmet>`; OG + Twitter tags; a real
   `og-image.png` (1200×630) in `assets/`.
4. **Structured data** — add an `Organization` + `WebSite` JSON-LD block to the
   home page.
5. **Sitemap** — one `<url>` per public page; submit in Search Console.
6. **Clean URLs** — `_redirects` owns every clean path on Cloudflare Workers
   static assets (keep `html_handling: "none"` in `wrangler.jsonc`). Add one
   line per new page.

---

## Fixed: `<helmet>` meta never reached the raw `<head>`

Found 29 Aug 2026 while building the per-retreat pages, fixed the same day by
`tools/apply_head_meta.py`. Kept here because the cause is a property of the
architecture and will come back the moment a page is written by hand.

Every page in this repo declares its `<title>`, description, canonical and
Open Graph tags inside `<x-dc><helmet>`, which is **in the body**. `support.js`
moves them into `document.head` when it renders. That is fine for anything that
runs JavaScript — Googlebot does — and useless for anything that does not,
which is every link-preview crawler there is: WhatsApp, iMessage, Slack,
Facebook, LinkedIn, Discord, Signal.

    curl -s https://paititi-institute.org/retreats \
      | python3 -c "import sys,re;h=sys.stdin.read();print(len(re.findall('og:',h[:h.find('</head>')])))"
    0

So a link to any page pasted into a chat showed a bare URL, with no title, no
description and no image. The browser tab showed the URL too, until the page
rendered.

**The fix** is `tools/apply_head_meta.py`. It moves the title, description,
robots, canonical/hreflang, `og:*`, `article:*` and `twitter:*` tags — and only
those — out of `<helmet>` and into the real `<head>`. Everything else
(stylesheets, icons, manifest, `theme-color`, the page's own `<style>`) stays in
`<helmet>`, which is where the runtime wants it. `gen_retreats.py` writes its
pages that way to begin with.

It also repairs three things that stop a card rendering even once the tags are
visible:

- `og:image` was a **site-relative path**; the spec wants an absolute URL and
  several scrapers drop a relative one.
- The images are **WebP**, which LinkedIn and older Mail/Messages builds render
  as nothing. Each now has a JPEG derivative under `assets/social/`, longest
  side 1200, uncropped.
- The **fourteen blog posts had no `og:image` at all** — the most-shared pages
  on the site. Each takes the first photograph in its own body.

`og:url` and `twitter:card` are filled in where they were missing.

### Where it sits in the pipeline

    migrate_blog.py -> gen_responsive.py -> apply_hreflang.py -> apply_head_meta.py

`apply_head_meta.py` runs **last** and is idempotent, so re-running it after any
of the others is the fix for the drift they cause. `migrate_blog.py --check`
imports `transform()` from it rather than trying to describe what it does, so
its byte-for-byte comparison stays honest.

**Writing a page by hand?** Put the meta straight in `<head>` (copy a
`Retreat-*.dc.html`), or write it in `<helmet>` and run
`python3 tools/apply_head_meta.py`. Either way, `--check` will tell you.

### Still worth doing

`og:image:alt` is set only on the retreat pages. The rest would need real
alternative text per image, which is a writing job rather than a scripted one.

---

## AI search, 21 Sep 2026

Search engines read prose. Answer engines — ChatGPT, Claude, Perplexity,
Gemini's AI Overviews — assemble an **entity** first and then answer questions
about it. The site was in good shape for the first and had almost nothing for
the second. Three things were added; all three are generated, idempotent and in
`npm run check`.

### 1. The entity: `tools/apply_schema.py`

Nothing on the site told a machine, in so many words, that Paititi Institute is
a nonprofit, that Roman Hanis founded it in 2010, that the Instagram account and
the YouTube channel and this website are one organisation, or that the reserve
is 1,516 hectares. A human reading `/about-us` knew all of it. Nothing else did.

The tool writes one schema.org `@graph` into the real `<head>` of all 76 public
pages: an `Organization`, the `WebSite`, a typed `WebPage`, a `BreadcrumbList`
on the 43 nested URLs, and a `BlogPosting` on the 14 article pages — using the
author and publication date that had been sitting unread in
`data/blog/posts.json` since the migration.

**The trap it is written around, and the one thing not to "fix":** EIN
31-1796801 belongs to **Empowerment WORKS**, the fiscal sponsor. Paititi is a
fiscally sponsored project and holds no 501(c)(3) or EIN of its own. Structured
data is precisely what an answer engine repeats without hedging, so a `taxID`
there would produce the sentence "Paititi Institute, EIN 31-1796801" in front of
donors and grant officers. The relationship is modelled as a `funder` and stated
in prose instead. The module docstring says this too, at length, on purpose.

### 2. The link graph: `tools/apply_crawl_nav.py`

`SiteHeader` and `SiteFooter` are `<dc-import>`s, fetched and rendered at
runtime. Everything *else* on a page is real HTML in the source, which is why
nobody noticed. Fetched the way a non-rendering crawler fetches it, the home
page offered **eight** internal links — the ones hand-written into its own body.
The forty in the nav did not exist yet.

Googlebot renders JavaScript, so ordinary search never saw this. Bingbot's fast
path and most AI crawlers do not, and to them the site was eighty pages that
barely link to each other. The sitemap gets pages *found*; it says nothing about
which pages belong together, which is the relationship an answer engine uses to
decide whether the Q'ero page and the reserve page are one body of work or two
unrelated documents.

The fix uses a property of the runtime: `<dc-import>` children are passed to the
component as props, and neither component renders children, so a link list
written inside the element is **kept in the source and dropped from the rendered
page**. JavaScript on, you get the real footer; JavaScript off, you get a plain
list of the same links; no rendering at all, a crawler reads them. That is
progressive enhancement, not cloaking — the links are the real ones and the
agent that renders gets strictly more, not less.

Verified by rendering nine pages across both trees in headless Chrome: the
fallback was absent from every DOM and the real footer present in every one, and
a DOM diff of `/team` with and without both new blocks came back at three lines,
all of them the invisible `<head>` JSON-LD. Raw-HTML internal links went 8 → 19.

The list is **parsed out of `SiteHeader`/`SiteFooter`** rather than kept in the
tool, so it cannot disagree with the real navigation.

### 3. `llms.txt` and `robots.txt`

`/llms.txt` is a Markdown map of the site at a conventional path, generated by
`apply_schema.py` from the same canonical/title/description the pages carry, so
it cannot list a page that does not exist or miss one that does. It leads with
the facts an assistant gets wrong otherwise — founding, legal status, the
sponsor's EIN *not* being ours, the reserve, the two language trees.

`robots.txt` now names the AI crawlers explicitly and allows all of them. It
granted nothing new — the wildcard already did — but it records the decision,
and two of those tokens are not crawlers at all: `Google-Extended` and
`Applebot-Extended` control whether already-crawled pages may be used for AI
answers, and disallowing them would remove the site from Gemini and Apple
Intelligence while leaving search untouched. That is a failure nobody would ever
trace back to that file. The comments in it explain the distinction between the
answer-engine agents and the bulk training agents, in case the policy is ever
revisited.

### Pipeline

    migrate_blog.py -> gen_responsive.py -> apply_hreflang.py
      -> apply_head_meta.py -> apply_analytics.py
      -> apply_crawl_nav.py -> apply_schema.py

`apply_schema.py` runs **last**: `apply_head_meta.py` inserts the preview tags
before the first `<script>` in `<head>`, and the `@graph` is a `<script>`.
`gen_retreats.py` and `migrate_blog.py` both compare *without* the two new
blocks, the same way they already did for the Google tag — and `apply_crawl_nav`
needs one extra allowance, because its block sits *inside* the SiteFooter import
and removing it leaves the indentation behind.

---

## For Roman: the content side

None of this was applied — it is all wording, and wording is Roman's. Ordered by
what an answer engine would gain.

**1. The site contradicts itself about Roman's title.** `/about-us` says
"Founder & President" in the governance section. `/team` says "co-founder" five
times and "Founder & President" once. An answer engine asked "who founded
Paititi Institute" has to pick one, and inconsistency is the main reason these
systems hedge. The structured data currently says `founder`, following the
governance section as the more formal statement. Pick one and make both pages
agree — it does not matter much which.

**2. There is no FAQ anywhere on the site.** This is the single biggest
remaining gap, and the format answer engines quote from most readily, because a
question heading followed by a direct answer needs no interpretation. The
questions people actually arrive with, none of which the site answers in one
place: is ayahuasca legal in Peru; what happens in a 16-day immersion, day to
day; what medical or psychiatric conditions rule someone out; what does it cost
and what is included; how do you get to the centre; is my donation
tax-deductible (the fiscal-sponsorship answer, which is genuinely confusing and
currently only inferable); what happens to the money; who are the Yahua and the
Q'ero and what is Paititi's relationship to them. Each is a heading and two to
four sentences. `apply_schema.py` can emit `FAQPage` markup for them the day the
answers exist — that part is a small change, and the writing is the work.

**3. Answer-first openings.** Several pages open with atmosphere and reach the
fact in paragraph three. `/initiatives/paititi-biocultural-reserve` is the clear
case: the 1,516 hectares, the altitude range and the Manu buffer are the
quotable facts, and they arrive after the scene-setting. Nothing needs cutting —
a single opening sentence that states what the page is about, before the prose
that makes you care, is enough, and it is what gets extracted.

**4. The Journal is seven posts, the newest from July 2025.** Recency and depth
both count for AI citation, and seven posts is thin for a twenty-year-old
organisation with this much field experience. Not an SEO task so much as the
thing that would most change the site's standing if there were appetite for it.

**5. `og:image:alt` and image alt text on the older pages** (see above) — a
writing job, and worth doing whenever those pages are next edited.

### What was checked and is already fine

Titles and descriptions are unique, well-sized and specific on all 80 pages;
hreflang and canonicals are correct in both trees; the sitemap is complete;
alt text on the newer pages is genuinely descriptive; page content is
server-rendered and readable without JavaScript. None of that needed touching.
