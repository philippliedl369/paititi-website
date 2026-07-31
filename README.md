# Meristem — zero-build marketing-site starter

A self-contained starter for a modern marketing site: clone it, serve it, and
everything renders with **no build step**. Pages are single HTML files composed
from a token-driven design system; dynamic pieces (WebGL, React widgets) embed
as pre-built "islands".

Extracted from a production site; all branding has been replaced with a
neutral placeholder theme (ink + emerald, Space Grotesk + Inter) that you
swap for the real brand in one place.

---

## Quick start

The pages fetch scripts and the design-system bundle over HTTP, so **serve the
folder, don't open files with `file://`**:

```bash
python3 -m http.server 8000   # …or: npx serve .
```

Then open **http://localhost:8000/Home.dc.html** (or `/` on a host that maps
clean URLs via `_redirects`).

## What's in here

```
meristem/
├── index.html            # Entry splash → redirects to the home page
├── Home.dc.html          # Skeleton home page (hero + island, cards, stats, CTA)
├── SiteHeader.dc.html    # Shared sticky header (imported by every page)
├── SiteFooter.dc.html    # Shared footer
├── support.js            # Design Component runtime (do not edit)
├── reveal.js             # Enter-once scroll reveals (tag sections with data-enter)
├── anchor-scroll.js      # Smooth anchor handling for client-rendered pages
├── image-slot.js         # Drag-and-drop image placeholder helper
├── _ds/meristem-design-system/   # ★ Tokens + component bundle (retheme here)
├── islands/              # Built, committed island bundles (shader-backdrop)
├── islands-src/          # React/Vite source for islands (rebuild: npm run build)
├── islands-demo.html     # Working island demo
├── docs/                 # Page architecture + SEO checklist
├── _redirects · _headers · wrangler.jsonc   # Cloudflare Workers static hosting
├── Dockerfile · nginx.conf.template · railway.json  # Alternative Docker hosting
└── robots.txt · sitemap.xml · site.webmanifest · .nojekyll
```

## Make it yours

1. **Retheme** — edit `_ds/meristem-design-system/tokens/*.css` (colors, type
   scale, fonts, spacing, effects). Keep the token names; pages and the
   component bundle consume the semantic aliases (`--text-heading`,
   `--accent-primary`, …).
2. **Rename** — find-and-replace `meristem`/`Meristem` and the `MeristemDS` /
   `MeristemIslands` globals if you want your own namespace.
3. **Content** — replace the placeholder copy in `Home.dc.html`, add pages
   (see `docs/design-system.md`), extend `_redirects` and `sitemap.xml`.
4. **Domain + SEO** — work through `docs/seo.md`; every page currently ships
   `noindex` and `example.com` placeholders on purpose.
5. **License** — this starter ships without one; add a `LICENSE` before
   publishing anything.

## Deployment

Any static host works. Cloudflare Workers static assets is preconfigured
(`wrangler.jsonc` — note `html_handling: "none"` is load-bearing; `_redirects`
owns all clean-URL rewrites). `_redirects` covers Netlify too; see
`docs/seo.md` for Vercel/Nginx/Apache, and keep `.nojekyll` on GitHub Pages.

## Islands

Author dynamic widgets in React under `islands-src/`, build them into
self-contained ES-module bundles in `islands/`, and mount them from any page:

```html
<div data-island="shader-backdrop" style="position:absolute;inset:0"></div>
<script type="module" src="/islands/shader-backdrop.js" defer></script>
```

```bash
cd islands-src && npm install && npm run build   # writes ../islands/*.js
```
