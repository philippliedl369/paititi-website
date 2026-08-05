# Paititi Institute — website

Replica of [paititi-institute.org](https://paititi-institute.org) rebuilt off
Squarespace onto the zero-build Meristem architecture: single-file
Design-Component pages (`.dc.html`) + a Cloudflare Worker that replaces every
function Squarespace used to provide.

## Where it runs

The same repo deploys to either platform. `api.js` holds the API logic; each
platform gets a thin adapter around it, so the two can't drift.

| | Cloudflare Workers | Node host (Railway, Render, Fly) |
|---|---|---|
| entry | `worker.js` (`wrangler deploy`) | `server.js` (`npm start`) |
| clean URLs | `_redirects`, read by the platform | `_redirects`, parsed by `server.js` |
| headers | `_headers`, read by the platform | `_headers`, parsed by `server.js` |
| newsletter store | KV namespace `NEWSLETTER` | `RESEND_AUDIENCE_ID`, or `NEWSLETTER_FILE` |

On Railway, set the variables under **Variables**: `RESEND_API_KEY`,
`STRIPE_SECRET_KEY`, `CONTACT_TO`, `SITE_ORIGIN` and `RESEND_AUDIENCE_ID`.
Railway detects `package.json` and runs `npm start`; `PORT` is injected.

Note that Railway's filesystem is ephemeral — `NEWSLETTER_FILE` only survives
redeploys if you mount a volume, so prefer a Resend audience in production.

## Quick start

The pages fetch scripts and the design-system bundle over HTTP, so **serve the
folder, don't open files with `file://`**:

```bash
npm start                          # Node server — clean URLs + /api/* (PORT=8080)
npx wrangler dev                   # same site on the Cloudflare runtime
python3 -m http.server 8000        # bare static preview: no clean URLs, no /api/*
```

Then open http://localhost:8000/Home.dc.html (or `/` under wrangler, which
maps clean URLs via `_redirects`).

## What replaced each Squarespace function

| Squarespace feature | Replacement |
|---|---|
| Newsletter block ("Sign up for updates") | Footer form → `POST /api/newsletter` (worker.js) → KV `NEWSLETTER` or Resend audience |
| Contact form | `Contact.dc.html` → `POST /api/contact` → email via Resend to `CONTACT_TO` |
| Store + cart + checkout (US Tour RSVP $300) | `Store.dc.html` / `StoreProduct-UsTour.dc.html` (14-field intake form) / `Cart.dc.html` (`cart.js`, localStorage) → `POST /api/checkout` → Stripe Checkout. Catalog: `data/products.json` (server-side price validation) |
| Donation block (Q'ero page: 2 funds, presets, recurring) | Rebuilt in place on `InitiativeQero.dc.html` → `POST /api/checkout` → Stripe, one-time or weekly/monthly/quarterly/annual. There is no `/donate` page on the live site, so that path is a 301 |
| Zeffy donation embed (Yagua page) | Kept as-is — plain iframe, platform-independent |
| Retreat Guru listings (retreats / online courses) | Kept as-is — script embed + static fallback cards |
| Blog CMS (8 posts, 4 categories) | Statically generated: `tools/migrate_blog.py` pulls Squarespace `?format=json`, downloads images to `assets/blog/`, writes `Blog*.dc.html` |
| Announcement bar | Baked into `SiteHeader.dc.html` |
| Clean URLs / legacy URLs | `_redirects` (incl. old encoded category URLs, `/home`, `/the-institute`, `/s/*.pdf`) |

## Going live — secrets to set

```bash
npx wrangler secret put RESEND_API_KEY      # contact form + notifications
npx wrangler secret put STRIPE_SECRET_KEY   # store + donations
npx wrangler kv namespace create NEWSLETTER # then add kv_namespaces to wrangler.jsonc
npx wrangler deploy
```

Until the secrets exist the forms return a friendly "not configured yet"
error; everything else works statically. Optional: `RESEND_AUDIENCE_ID` to
push newsletter signups into a Resend audience instead of KV.

Before launch also work through `docs/seo.md` — every page currently ships
`noindex` on purpose; strip those metas when the domain cuts over.

## Assets

Every image the live site uses is mirrored locally — nothing loads from the
Squarespace CDN any more. `assets/manifest.json` is the source of truth: for
each asset it records where it came from, what it was originally called, which
pages use it, and its alt text.

```bash
python3 tools/sync_assets.py --report   # what's referenced vs. what's mirrored
python3 tools/sync_assets.py            # pull anything new (idempotent)
python3 tools/dedupe_assets.py --dry-run  # find duplicate copies of one image
```

`sync_assets.py` crawls the live pages, fetches each asset at `?format=original`,
and gives it a deterministic name — from the original filename when that carries
meaning, otherwise from the page it appears on (Squarespace names five different
photos `image-asset.jpeg`). Re-run it after uploading anything new in Squarespace.

Two things worth knowing:

- **The CDN only ever returns WebP, capped at 2500px.** Even requesting the
  source `.png` yields WebP. These files are exactly what visitors see today,
  but they are not the original masters. If you need print-resolution or the
  layered logo, export those from the Squarespace admin — that's the one thing
  scraping cannot reach.
- **The manifest is keyed by origin URL**, which is what makes reuse possible:
  `tools/migrate_blog.py` looks each blog image up there before fetching, so the
  blog references the same mirrored WebP as everything else. Skipping that
  lookup once cost 8MB of JPEGs duplicating files already in the repo.
- **`assets/brand/` is hand-curated** and deliberately excluded from
  `dedupe_assets.py`. The logo and favicon exist as both a WebP master and a
  PNG derivative (`sips -s format png`), because favicons and some clients
  still need PNG. The header uses the purple logo on light chrome, the footer
  the white one on the dark band.

## Layout

```
├── worker.js             # /api/contact · /api/newsletter · /api/checkout (Stripe)
├── data/products.json    # trusted price catalog for checkout
├── cart.js               # localStorage cart + checkout client
├── paititi.css           # the shared page shell: fluid grid, sections, type scale
├── Home.dc.html …        # one .dc.html per page (see _redirects for the map)
├── Blog*.dc.html         # generated — edit tools/migrate_blog.py and re-run instead
├── SiteHeader/SiteFooter.dc.html   # shared chrome (nav, announcement bar, newsletter)
├── _ds/meristem-design-system/     # tokens rethemed to Paititi (Philosopher/Lato, plum)
├── assets/               # all images localized from the Squarespace CDN
├── tools/migrate_blog.py # blog migration/regeneration script
└── _redirects · _headers · wrangler.jsonc   # Cloudflare Workers hosting
```

## Matching the original

Pages are not laid out in normal flow. Squarespace 7.1 positions every block on
a **fluid engine grid**, and `paititi.css` reproduces it: 24 content columns
across a 1200px column, 11px gaps, 25.7969px rows. Each block carries the live
`grid-area`, so a page is a transcription of measured coordinates rather than an
approximation:

```html
<section class="pt-sec" style="--pt-bg:#F1EAF6">
  <div class="pt-sec-bg"></div>
  <div class="pt-fluid" style="--pt-grid-top:48px;--pt-grid-bot:76px;--pt-rows:46">
    <div class="pt-prose" style="grid-area:5 / 6 / 16 / 20"> … </div>
  </div>
</section>
```

Sections carry their own background colour and are separated by a shallow sine
wave rather than a straight edge; `.pt-sec-bg` draws both. The per-section
values (`--pt-grid-top`, `--pt-grid-bot`, `--pt-rows`, and occasionally
`--pt-row-h` or zero gaps) are measured off the live page, not chosen.

Fidelity is checked by diffing every block's box against the live site. Two
sections deliberately differ: the Retreat Guru widgets on Retreats and Online
Courses render live listings, so their height follows real data.

**The commerce pages are the exception.** `/store`, `/store/retreats`,
`/store/p/…`, `/cart` and `/order-confirmed` are Squarespace *commerce* and
*system* pages: no fluid grid, no wave divider, white ground, a 1324.8px
measure instead of the 1200px column. Their system lives in `store.css`; the
55px commerce button is `.pt-sqs-btn` in `paititi.css`. Nothing on the live
product page collects an application — the RSVP button only adds the $300
deposit to the cart — so this replica does the same, and the Stripe path
(`cart.js` → `/api/checkout`) is unchanged.

**Blog pages are generated.** Edit `tools/migrate_blog.py` and re-run it; never
edit `Blog*.dc.html`. The migration keeps Squarespace's own block scaffolding
verbatim, so `POST_CSS` has to reproduce that scaffolding's spacing rather than
replace it — the 17px block gutter with the row pulled out to match, the 16px
paragraph rhythm, image blocks as aspect-ratio boxes with the image out of
flow, and the two image-container variants (`has-aspect-ratio` reserves the
height, `content-fit` does not). Images are resolved through
`assets/manifest.json`, which is keyed by the origin CDN URL, so the mirrored
WebP is reused instead of re-downloading a JPEG copy.

The page model (Design Components, islands, motion) is documented in
`docs/design-system.md`; deployment details in the original starter notes
below.

## Deployment

Cloudflare Workers static assets + worker (`wrangler.jsonc`):

```bash
npx wrangler deploy
```

`html_handling: "none"` is load-bearing — `_redirects` owns all clean-URL
rewrites. `_headers` and `_redirects` in the root are picked up automatically;
`.assetsignore` keeps the toolchain (incl. `tools/`) out of the published
assets.
