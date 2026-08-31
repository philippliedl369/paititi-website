# Project: Paititi Institute website

## What this is

The live site at **paititi-institute.org**, rebuilt off Squarespace onto the
zero-build Meristem architecture: single-file Design-Component pages
(`.dc.html`) served by a Cloudflare Worker. Bilingual — English at the root,
Spanish under `/es/`. No build step, no CI, no staging gate: the repo is the
site.

Two people work here (Philipp, Roman), both with AI, both able to publish. That
is why this file exists — the traps below fail *silently*, so an edit that looks
right in the editor and right in one browser can still be wrong on the live
site for a week before anyone notices.

## Read first

- **README.md** — the full picture: what replaced each Squarespace function,
  the Spanish tree, the asset pipeline, the fluid-engine layout, mobile,
  deployment. Long, and worth it. Most "how does X work" questions are answered
  there.
- **build-spec.md** — the *content* authority. Roman's decisions, settled
  wording, open blockers. Not published (see `.assetsignore`). When copy and
  this file disagree about a fact, build-spec wins.
- **docs/design-system.md** — the page model (Design Components, islands,
  motion). **docs/seo.md** — meta, indexing, the head-meta fix.
- **docs/living-wisdom-school.md**, **docs/cloudflare-migration.md**,
  **docs/motion.md**, **docs/asset-wishlist.md** — as needed.

## Publishing

```bash
git push                 # changes nothing on the live site
npx wrangler deploy      # this is what publishes
```

There is no CI. A push is not a deploy and a deploy is not a push — do both, in
that order. `wrangler deploy` uploads the **working folder**, not the commit, so
anything lying around uncommitted goes live too.

`npx wrangler rollback` undoes the last deploy. Know this one by heart.

`.assetsignore` decides what is *not* published. Read its comments before
changing it: patterns are gitignore rules, so an unanchored `docs/` matches at
any depth and once silently 404'd a linked PDF for a week. It is also what
holds `LivingWisdomSchool*.dc.html` back from the live site — that page is
finished and deliberately unpublished until Roman settles how it is introduced.
Don't "fix" its absence.

## Never hand-edit these — they are generated

| File | Regenerate with |
|---|---|
| `Blog*.dc.html`, `BlogPost-*`, `BlogCategory-*` | `data/blog/*.json` → `tools/migrate_blog.py` |
| `Retreat-*.dc.html` | `data/retreats*.json` → `npm run gen-retreats` |
| `sitemap.xml`, the hreflang blocks, each page's `sister` prop | `tools/i18n_pairs.json` → `tools/apply_hreflang.py` |
| `assets/r/**` and every `srcset`/`sizes` attribute | `tools/gen_responsive.py` |

Editing the output instead of the source works exactly until the next
generator run erases it.

**Pipeline order matters:** `migrate_blog.py` → `gen_responsive.py` →
`apply_hreflang.py` → `apply_head_meta.py` → `apply_analytics.py`. The last two
are idempotent and rewrite `<head>`, so they run in that order and at the end.
`apply_hreflang.py --check`, `migrate_blog.py --check` and
`apply_analytics.py --check` verify without writing.

**A new page needs the Google tag.** `apply_analytics.py` puts the GA4 tag
(`GT-MBL4BMP`) in the real `<head>` of all 80 pages. It has to be in the source
HTML, not `<helmet>` and not behind a wrapper file — Google's "is the tag
installed?" check reads the HTML as it arrives, the same way link-preview
crawlers do, and reports *Not detected* for anything that only appears after
JavaScript runs. Re-run it after adding a page; `--remove` takes it back out.

**Google Ads conversions live in `conversions.js`,** loaded by that same block.
It counts clicks through to Retreat Guru and Zeffy plus the two form
submissions — the Ad Grant requires at least one conversion, and does not
accept a bare page view as the only one. Three of its four label slots are
still `null` until Roman creates those actions in Ads; a `null` slot sends
nothing and breaks nothing. Two traps it is already written around, both of
them in the list below: Google's own snippet expects an inline `onclick`, which
the DC runtime strips, and a listener bound to an element does not survive the
re-render — so it delegates from `document`. Don't hardcode `value`/`currency`
either; that belongs on the action in the Ads UI, where changing it is not a
deploy.

## The silent failures

None of these throw an error. All of them have shipped at least once.

1. **`<helmet>` meta is invisible to link-preview crawlers.** Every page
   declares its title, description and `og:*` inside `<x-dc><helmet>`, which is
   in the *body*; `support.js` moves it to `<head>` at runtime. WhatsApp,
   iMessage, Slack, LinkedIn and Facebook run no JavaScript and see nothing.
   **Any change to a page's title, description or social image must be followed
   by `python3 tools/apply_head_meta.py`.** See docs/seo.md.
2. **`sc-if` / `sc-for` typos do nothing.** A misspelled DC attribute does not
   warn — the conditional simply never fires and the element renders (or
   doesn't) forever.
3. **Colour on element selectors in `paititi.css` makes text invisible.**
   Specificity must match the base scale: `.pt-page main h1`, never
   `.pt-page h1`. Written short it loses at every width and silently does
   nothing — this is how an h1 rendered at 64px on a 390px phone. The comment
   at the top of `paititi.css` explains it.
4. **Letter-spacing is load-bearing.** It is declared once in `em` at the root
   and inherited as px. Setting it anywhere else rescales it, rewraps every
   paragraph, and moves all vertical geometry below.
5. **Data-URI SVGs in CSS get their `viewBox` mangled.** Use a file.
6. **Inline `onclick` does not survive the DC render.** The runtime strips
   event-handler attributes, so a handler written into a `.dc.html` file is
   simply gone from the rendered page — no error, no warning, a link that
   does nothing. Bind from a script instead, and prefer a delegated listener
   on `document`: the page is re-rendered out of `<x-dc>` after load, which
   detaches anything bound directly to an element. `consent.js` is the worked
   example.

## Layout: the geometry is measured, not chosen

Above 1180px, pages are transcriptions of the live Squarespace fluid grid —
24 columns, 1200px measure, 25.7969px rows — with each block's real
`grid-area`. Values like `--pt-rows` and `--pt-grid-top` were *measured*, not
picked. Don't tidy them.

Below 1180px it is a different layout entirely (flex columns, `@media` blocks
at the foot of `paititi.css` plus a 640px block per page), and nothing there is
a transcription of anything.

**The test for any layout change: diff every block's box at 1440px before and
after, and expect zero movement.** Verify phones with Chrome DevTools Protocol
emulation — a `--window-size=390` screenshot is a crop, not a phone.

Pages added after the replica — `/retreats/<slug>`, Distance Healing, Living
Wisdom School — have no live counterpart and are *composed* in flow rather than
measured. Don't try to match them to anything.

## Bilingual

Every English page has an `*.es.dc.html` twin; there is no runtime translation
layer. **A change to one side is only half done.** `tools/i18n_pairs.json` is
the single source for pairs and drives hreflang, the EN/ES switcher and the
sitemap.

- Slugs are translated (`/es/quienes-somos`); **in-page anchor ids stay in
  English** (`#impact`, `#packages`) so both trees share one anchor map.
- A pair is annotated only when both halves exist, so a half-built translation
  never advertises a 404.
- Some things stay in English on purpose (the book title, film and article
  titles, Retreat Guru, Zeffy, JotForm). **Never label them as English** — no
  "(en inglés)". A page announcing its own language reads as an apology.

## Images

- Masters live in `assets/`, mirrored from the old CDN and recorded in
  `assets/manifest.json` (keyed by origin URL — always look there before
  fetching anything). The CDN only ever returned **WebP capped at 2500px**;
  these are not print masters.
- Never drop a raw photo into `assets/` and reference it directly. Run
  `tools/gen_responsive.py` so it gets a width ladder — otherwise a phone
  downloads the full desktop file.
- `sizes` values in `tools/image-sizes.json` are *measured* in a headless
  browser. Re-measure if the layout moves; a guessed `sizes` silently serves
  the wrong file.
- `assets/brand/` is hand-curated and excluded from dedupe. Social cards need a
  **JPEG** derivative in `assets/social/` — LinkedIn and older Mail render WebP
  as nothing.

## Settled content decisions

From build-spec.md — do not relitigate:

- Beyond Ayahuasca funding, verbatim site-wide: "100% of Roman Hanis' author
  royalties from Beyond Ayahuasca support Paititi Institute's Indigenous
  education and cultural preservation initiatives."
- Nav labels: **Journal** (URL stays `/blog`) and **Support** (not Donate).
- The reserve is **1,516 hectares** everywhere.
- The Team page is Roman-only. Closed subject.
- Forms must never leak internals — the visitor-facing error text comes from
  `api.js` and may not name secrets, providers or product ids.

## Before you deploy

1. Serve it locally and actually look: `npm start` (clean URLs + `/api/*`) or
   `python3 -m http.server 8000`. Never open `.dc.html` over `file://` — module
   fetches are blocked and the page won't render.
2. Check the page at 1440px **and** on an emulated phone.
3. If a title, description or social image changed: `npm run head-meta`.
4. If anything was generated: re-run the pipeline in order.
5. Both languages touched?
6. `git push` **and** `npx wrangler deploy`.

## Two people, one repo

Pull before starting, push as soon as you're done. Merge conflicts inside a
3000-line `.dc.html` are genuinely nasty and should never be resolved
unsupervised — if one appears, stop and ask rather than guessing which side
was right.
