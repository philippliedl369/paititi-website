# Paititi Institute — website

Replica of [paititi-institute.org](https://paititi-institute.org) rebuilt off
Squarespace onto the zero-build Meristem architecture: single-file
Design-Component pages (`.dc.html`) + a Cloudflare Worker that replaces every
function Squarespace used to provide.

## Quick start

The pages fetch scripts and the design-system bundle over HTTP, so **serve the
folder, don't open files with `file://`**:

```bash
python3 -m http.server 8000        # static preview (no /api/*)
npx wrangler dev                   # full preview incl. Worker API routes
```

Then open http://localhost:8000/Home.dc.html (or `/` under wrangler, which
maps clean URLs via `_redirects`).

## What replaced each Squarespace function

| Squarespace feature | Replacement |
|---|---|
| Newsletter block ("Sign up for updates") | Footer form → `POST /api/newsletter` (worker.js) → KV `NEWSLETTER` or Resend audience |
| Contact form | `Contact.dc.html` → `POST /api/contact` → email via Resend to `CONTACT_TO` |
| Store + cart + checkout (US Tour RSVP $300) | `Store.dc.html` / `StoreProduct-UsTour.dc.html` (14-field intake form) / `Cart.dc.html` (`cart.js`, localStorage) → `POST /api/checkout` → Stripe Checkout. Catalog: `data/products.json` (server-side price validation) |
| Donation block (Q'ero page: 2 funds, presets, recurring) | `Donate.dc.html` → Stripe Checkout, one-time or weekly/monthly/quarterly/annual |
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
├── Home.dc.html …        # one .dc.html per page (see _redirects for the map)
├── Blog*.dc.html         # generated — edit tools/migrate_blog.py and re-run instead
├── SiteHeader/SiteFooter.dc.html   # shared chrome (nav, announcement bar, newsletter)
├── _ds/meristem-design-system/     # tokens rethemed to Paititi (Philosopher/Lato, plum)
├── assets/               # all images localized from the Squarespace CDN
├── tools/migrate_blog.py # blog migration/regeneration script
└── _redirects · _headers · wrangler.jsonc   # Cloudflare Workers hosting
```

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
