# Design system & page architecture

How the site is built and how to add to it. The design system itself lives in
[`_ds/meristem-design-system/`](../_ds/meristem-design-system/readme.md); this
doc covers the page model around it.

## The page model: Design Components (`.dc.html`)

Each page is a single self-contained HTML file that renders live in the
browser — no build step. `support.js` (the DC runtime, do not edit) turns the
`<x-dc>` markup into a rendered page:

- `<helmet>` — everything destined for `<head>`: title, meta, the design-system
  stylesheet/bundle links, page-local `<style>`.
- Page body — plain HTML styled with design-system tokens (`var(--…)`), plus
  `<x-import component-from-global-scope="MeristemDS.X">` for components.
- `<dc-import name="SiteHeader">` / `SiteFooter` — shared fragments; edit
  `SiteHeader.dc.html` / `SiteFooter.dc.html` once and every page updates.
- A trailing `<script type="text/x-dc" data-dc-script>` — the page's logic
  class (props, state, `renderVals()`); template slots `{{ name }}` bind to it.
- `sc-for` / `sc-if` — list and conditional rendering in templates.

### Adding a page

1. Copy `Home.dc.html`, keep the `<helmet>` boilerplate, replace the content.
2. Add a clean-URL line to `_redirects` (`/pricing /Pricing.dc.html 200`).
3. Add the page to `sitemap.xml` and link it from the header/footer.

## Motion

- `reveal.js` — enter-once scroll reveals. Tag a whole section container with
  `data-enter`; heading and body rise together, once, then latch. The first
  section under the hero stays untagged (it should already be at rest when the
  reader arrives). With `prefers-reduced-motion` or no JS, pages rest in their
  final designed state.
- `.ink-rule` — the highlight underline on section headings; part of the
  resting design, reveal.js only animates its first draw.
- `anchor-scroll.js` — smooth in-page anchor handling that survives the
  client-side render.

## Islands (dynamic widgets)

The site stays zero-build; dynamic pieces are authored in React under
`islands-src/` and built into `islands/*.js` as self-contained ES-module
bundles. A page opts in with two lines:

```html
<div data-island="shader-backdrop" style="position:absolute;inset:0"></div>
<script type="module" src="/islands/shader-backdrop.js" defer></script>
```

Each island is built in isolation (one Vite run per entry, `ISLAND` env var)
so every bundle keeps its own React and no shared chunk is hoisted. The built
bundles are committed; the toolchain is excluded from deploys via
`.assetsignore`. Add an island: new entry in
`islands-src/src/`, register it in `ENTRIES` in `vite.config.ts`, extend the
`build` script, then `npm run build`.

## Working locally

Serve the folder (module fetches are blocked under `file://`):

```bash
python3 -m http.server 8000   # or: npx serve .
```
