# Meristem Design System

The single source of truth for how this site looks. Everything on every page
composes this system — no page invents its own colors, type, spacing, or
components.

> **Placeholder brand.** The current tokens are a neutral, modern starter
> palette (ink + emerald + mint, Space Grotesk + Inter). Replace the values in
> `tokens/*.css` with the real brand when it exists; keep the token *names* and
> the semantic aliases, because the component bundle consumes them.

## What's here

- `tokens/` — colors, typography, spacing, fonts, effects. Edit these to
  retheme the whole site.
- `styles.css` — the one file pages link; imports all tokens in order.
- `_ds_bundle.js` — the component library, exposed on `window.MeristemDS`:
  Button, Icon, IconButton, Badge, Card, Tag, Callout, Dialog, Tooltip,
  Checkbox, Input, Radio, Select, Switch, Textarea, Tabs.
- `_ds_manifest.json` / `_adherence.oxlintrc.json` — tooling metadata and the
  lint config that flags raw hex colors / px values that bypass tokens.

## Using it in a page

Link the tokens and bundle in the page's `<helmet>` (copy the block from
`SiteHeader.dc.html`), then compose components:

```html
<x-import component-from-global-scope="MeristemDS.Button" variant="primary" size="md">Label</x-import>
```

Button variants: `primary | secondary | ghost | link`; sizes `sm | md | lg`.
Card tones: default (white), `mist` (light surface), `navy` (inverse/ink —
the tone names are the component API and predate the retheme; they map to
`--surface-section` and `--surface-inverse`).

## Rules

- **No raw hex, no raw px** in page markup where a token exists — use
  `var(--…)` semantic aliases (`--text-heading`, `--surface-section`,
  `--accent-primary`, …).
- Headings use `font: var(--text-h1…h4)`; body text uses `--fs-body`/`--lh-body`.
- Components come from `MeristemDS.*` — don't re-style raw HTML to imitate them.
