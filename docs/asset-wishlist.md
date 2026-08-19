# Asset wishlist — what to export by hand

Everything the live site loads is already mirrored (see `assets/manifest.json` and
the README's Assets section). This file lists the images that are worth
**replacing with a better original**, because the version Squarespace holds is
smaller than the box the site displays it in — those are soft on
paititi-institute.org today, not just here.

Verified 2026-08-04 against the live pages at 1440px. For each one the CDN was
re-queried at `?format=original`, `2500w` and `1500w`; none returns anything
larger, so the low resolution is in the uploaded file itself. Re-uploading in
Squarespace will not help either — drop the replacement straight into `assets/`
under the target name below and re-run `python3 tools/sync_assets.py --report`.

Target width = 2× the largest box the image is displayed in, so it stays sharp
on retina.

## 1. Displayed larger than it is — visibly soft today

| # | current file | what it is | now | shown at | want | save as |
|---|---|---|---|---|---|---|
| 1 | `home/maloka-interior-paititi-institute-iquitos-peru-greg-goodman-.webp` | maloka interior — **the footer background on every page** | 678×446 | 1440×833 | ≥2880w | keep name |
| 2 | `home/dreamworksacredgeometry-square.webp` | pink flower fractal — **slideshow slide 2** | 841×473 | 1438×809 | ≥2880w | keep name |
| 3 | `retreats/beyond-ayahuasca-01.webp` | Yagua community holding *Beyond Ayahuasca* — used on 3 pages | 1099×679 | 1440×969 | ≥2880w | `yagua-community-with-books.webp` |
| 4 | `store/9f81c-coca-ceremony-paititi-institute-iquitos-peru-greg-good.webp` | night ceremony circle in the maloka | 600×400 | 662×883 | ≥1800w | `maloka-ceremony-night.webp` |
| 5 | `blog/blog-03.webp` | illustration, figure beside a ravine | 200×200 | 518×346 | ≥1040w | `illustration-ravine-figure.webp` |
| 6 | `blog/blog-04.webp` | visionary portrait of an elder | 500×500 | 518×346 | ≥1040w | `visionary-portrait-elder.webp` |
| 7 | `blog/blog-05.webp` | campfire circle at night | 500×500 | 518×346 | ≥1040w | `campfire-circle-night.webp` |
| 8 | `blog/screenshot-2025-12-03-at-115430-am.webp` | the Substack logo | 210×134 | 292×431 | SVG | `brand/substack-logo.svg` |
| 9 | `initiatives/distance-healing.webp` | clinic treatment session | 1404×936 | 1440×932 | ≥2880w | keep name |

Number 8 is a logo, not a photograph — take the SVG from Substack's brand page
rather than a screenshot, and file it under `assets/brand/`.

## 2. Not from Squarespace at all

Five thumbnails come from the Retreat Guru widget, so they can't be exported
from the Squarespace admin — they have to be replaced inside Retreat Guru, and
they are served at 300×300:

- `ETNcircle-300x300.jpg` — /retreats
- `DreamworkSacredGeometry-SQUARE-300x300.jpg` — /online-courses
- `stone-tower-square-300x300.jpg` — /online-courses
- `Sacred-Spiral-sq-300x300.jpg` — /online-courses
- `Amazonian-Shaman-in-Mystical-Rainforest-200x300.png` — /online-courses

## 3. Fine for the web, but not masters

Twelve assets sit exactly at the CDN's 2500px ceiling, so the mirrored copy is
a downscale of whatever was uploaded. They are all displayed at ≤1440px, so
nothing looks soft — only re-export these if you need print resolution:

`home/screenshot-2025-04-12-at-70237e280afpm.webp` (the homepage hero) ·
`home/paititi-lizpeace-63.webp` · `home/discoverpaititi-01.webp` ·
`about/paititi-lizpeace-190.webp` · `about/roman-ancelmo-book.webp` ·
`blog/unsplash-image-jwn0vkrklvk.webp` · `blog/blog-01.webp` ·
`initiatives/unsplash-image-uo1hwtgi6ze.webp` and the four
`initiatives/screenshot-2025-08-01…` / `screenshot-2025-11-14…` files.

## 4. Missing subjects — wanted for the impact story (18 Aug 2026)

The /initiatives rework told the Reserve and Community Health chapters with the
only imagery that exists. These subjects have **no photo at all** in the mirror —
ask Roman for originals (≥2880w where they'll go full-bleed):

| subject | would replace / fill | save as |
|---|---|---|
| Reserve landscape (cloud forest, watershed, plots, nursery) | interim in place: `initiatives/reserve-valley.webp` (1000w, from the old Squarespace CDN) now sits on /initiatives — still want ≥2880w originals; the hummingbird loop remains on /about-us and /discover-paititi | `initiatives/reserve-…webp` |
| Clinic day — wide shot with patients waiting / brigade travelling | only one clinic photo exists (`initiatives/distance-healing.webp`) | `initiatives/clinic-…webp` |
| Yahua school in use — children learning inside the maloca | school photos are all of the empty building | `initiatives/school-…webp` |
| Q'ero present-day (not COVID relief) — despacho, elders, village | Q'ero imagery is all 2021 food-drive | `initiatives/qero-…webp` |

## Naming

Lowercase kebab-case, subject first, no dates, no capture-app prefixes
(`whatsapp-image`, `signal-`, `screenshot-`), no UUIDs. 89 of the 105 mirrored
assets already follow this; the 16 that don't are listed in
`tools/sync_assets.py`'s name map and are due for a rename pass.
