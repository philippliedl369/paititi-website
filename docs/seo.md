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

## Open: `<helmet>` meta never reaches the raw `<head>`

Found 29 Aug 2026, while building the per-retreat pages.

Every page in this repo declares its `<title>`, description, canonical and
Open Graph tags inside `<x-dc><helmet>`, which is **in the body**. `support.js`
moves them into `document.head` when it renders. That is fine for anything that
runs JavaScript — Googlebot does — and useless for anything that does not,
which is every link-preview crawler there is: WhatsApp, iMessage, Slack,
Facebook, LinkedIn, Discord, Signal.

    curl -s https://paititi-institute.org/retreats \
      | python3 -c "import sys,re;h=sys.stdin.read();print(len(re.findall('og:',h[:h.find('</head>')])))"
    0

So a link to any page pasted into a chat shows a bare URL, with no title, no
description and no image. The browser tab also shows the URL until the page
renders.

**The `/retreats/<slug>` pages do not have this problem**: `tools/gen_retreats.py`
writes their title and social card into the real `<head>` and leaves only the
stylesheets, icons and page CSS in `<helmet>`. They were built to be sent to
people one at a time, so the preview is the feature.

Everything else on the site still needs the same treatment. It is an additive
change — copy `<title>`, `description`, `canonical`, `og:*` and `twitter:*` up
into `<head>` — and the two generators that own those tags
(`tools/apply_hreflang.py`, `tools/migrate_blog.py`) would need to write them
there instead. Not done yet, deliberately: it touches all 62 pages and belongs
in its own change.
