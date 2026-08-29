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
