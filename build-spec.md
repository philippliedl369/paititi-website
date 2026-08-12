# Website redo — build spec (reconciled against this repo)

Written 11 August 2026, after auditing every page of this rebuild against Roman's
endorsed ChatGPT session (verbatim transcript received via WhatsApp, 11 Aug 11:28–11:40).
That session analysed the **old Squarespace site's indexed version**; this file replaces
it as the build authority because several of its findings are already fixed here, several
are not, and its Squarespace capacity constraints no longer apply. Deadline (Roman,
WhatsApp 11 Aug): **live before 20 August 2026**.

Roman-facing sign-off doc: published as an artifact (link in the working notes). His
remaining blockers are at the bottom; everything else is buildable without him.

## Answered by Roman's own 11 Aug messages (no longer blockers)

- **Beyond Ayahuasca funding line.** Roman: "the precise commitment is 100% of your
  author royalties, I would use exactly that everywhere." Standard sentence, now safe to
  apply site-wide: "100% of Roman Hanis' author royalties from Beyond Ayahuasca support
  Paititi Institute's Indigenous education and cultural preservation initiatives."
- **"Journal" is the nav label** (his endorsed nav says Journal; URL stays `/blog`).
- **"Support" is the nav label for the donate entry** (his nav says Support, not Donate).
- **Reserve figure**: standardise on 1,516 hectares (he asked for exactly this).
- **Team page roster**: not a topic. The Team page stays as it is in the rebuild
  (Roman only); ChatGPT's remove-Robin advice is void and the subject is closed
  (Philipp, 11 Aug).

## Audit result: what the rebuild already handles

Verified 11 Aug 2026 — do **not** re-do these:

- **No encoding artifacts.** Zero "eƯ"-type matches anywhere.
- **Distance Healing is consolidated.** paititidistancehealing.com is absorbed: tabbed
  `/distance-healing` page, two standalone payment pages (emailed, not browsed to), Home
  Study Course promo moved to `/online-courses#home-study-course`, all old DH paths 301
  in `_redirects`. Remaining DH questions are Roman decisions, not build work.
- **Homepage nonprofit legitimacy is in place.** Hero → Quechua quote + three stat
  bullets → nonprofit paragraph → Our Impact list with every org fact (20+ years,
  1,516 ha, APCI, 2,000+ clinic patients, 600+ COVID families, clean water, Supreme
  Court, Yahua school, royalties line).
- **Funding language is already standard on Home and About.** Both say "100% of the
  author's royalties" (Home.dc.html:195, AboutUs.dc.html:155). Only outliers below.
- **Clean-URL + redirect infrastructure exists** (`_redirects`, parsed by both worker
  and server), including legacy encoded blog-category URLs and the mindmap PDF path.

## Audit result: confirmed broken / missing (this is the work)

| # | Finding | Where |
|---|---------|-------|
| 1 | "4000 acre nature reserve" contradicts 1,516 ha, + "Permacutlure" typo | AboutUs.dc.html:185 (Earth Stewardship accordion), DiscoverPaititi.dc.html:182 |
| 2 | "A portion of the book's proceeds… cultural heritage center" contradicts the 100%-royalties line | BeyondAyahuasca.dc.html:133; softer variant in Team.dc.html:83 ("proceeds directly supporting") |
| 3 | Initiatives "Land — pantry and classroom" accordion repeats the "School" paragraph verbatim; Land lost its own copy | Initiatives.dc.html:143 + 150 |
| 4 | Online Courses listing is a Retreat Guru iframe → near-zero crawlable content (the ChatGPT critique still applies to the rebuild) | OnlineCourses.dc.html:110 |
| 5 | No mentorship page exists; "Book a Connection Call" is an unexplained mailto on Team | Team.dc.html:77 (`mailto:roman@…?subject=15 min connection call`) |
| 6 | Retreats page = hero + Himalayan Pilgrimage (Oct 17–31 2026, **no price shown**) + rbg iframe. No gateway framing, no reciprocity section | Retreats.dc.html |
| 7 | Homepage still has the two-offering carousel (Retreats / Online Courses, promising "Breathwork · Qi Gong · Evolutionary Blueprint") | Home.dc.html:126–176 |
| 8 | Nav is the old-site replica: The Institute ▾ (Initiatives · About Us · Team · Beyond Ayahuasca) · Events & Retreats · Online Courses · Distance Healing · Blog | SiteHeader.dc.html |
| 9 | **Every one of the 34 pages carries `noindex`** (staging guard) | all *.dc.html |
| 10 | No `404.html` — server.js:169 looks for it and falls back to plain text | repo root |
| 11 | Ancient Squarespace-era paths not in `_redirects`: `/courses`, `/stewardship/courses-retreats/`, `/education/peru-retreats-courses/`, `/paititi-family/`, `/who/paititi-centers/`, `/who/the-paititi-family/roman-hanis/`, `/who/partners/sacred-science/`, `/healing/indigenous-healing-center/`, `/journal/[slug]` | `_redirects` |
| 12 | Team page meta title is "Team 1 \| Paititi Institute"; bio typo "elders of the and Yahua tribe"; whole bio is `<strong>` | Team.dc.html:13, :85 |

## URL policy (supersedes the earlier proposed URL set)

The earlier spec proposed `/about`, `/courses`, `/journal`, `/support`. **Dropped.** The
rebuild replicates the live site's URLs exactly, which means the migration needs **zero
redirects for existing pages** — the strongest possible SEO position. Policy:

- **Keep every live URL**: `/about-us`, `/online-courses`, `/blog`, `/retreats`,
  `/beyond-ayahuasca`, `/initiatives`, `/distance-healing`, `/team`, …
- **Add** `/mentorship` (new page).
- **Add 301s, additions only**: `/courses → /online-courses` (fixes the old 404'ing
  path with live external links), `/journal → /blog`, plus the ancient paths in row 11
  above, targeted at their nearest current page.
- Nav labels are free to say "Journal" while the URL stays `/blog` (Roman decision #5).
- `/support` only if Roman wants a support page later; the Donate button targets the
  Yagua initiative page today and keeps doing so.

## Phase 1 — everything before 20 August

### 1.1 Navigation (SiteHeader.dc.html + SiteFooter)

Target, per the endorsed architecture:

> About | Programs ▾ | Initiatives ▾ | Beyond Ayahuasca | Journal | Support(=Donate)

- **Programs ▾**: Retreats · Online Courses · Individual Mentorship & Dreamwork ·
  Distance Healing (placement pending Roman #3; default = here) · Workshops & Events
  (label for the Retreat Guru events listing — can anchor `/retreats#events`)
- **Initiatives ▾**: Our Living Vision (`/initiatives`) · Yahua Ancestral School
  (`/initiatives/yagua-cultural-heritage-center-indigenous-school`) · Q'ero Initiative
  (`/initiatives/project-one-f5w4d-4nex6`) · Paititi Biocultural Reserve, Community
  Health & Natural Medicine, Impact → **anchors into existing pages** (`/initiatives#…`,
  `/#impact`). Do not build six subpages before the 20th.
- About → `/about-us`; Team stays reachable (under About dropdown or footer).
- Anti-goal (Roman-endorsed): no split identities, no "Roman" vs "nonprofit" areas.
- The header is one component — this is a single-file change plus per-page `active`
  values. Mobile menu mirrors the same structure.

### 1.2 Homepage "Ways to Walk With Us" (Home.dc.html)

Replace the two-slide carousel (lines ~126–176) with four cards (copy from Roman's
endorsed session, usable as-is):

1. **Immersive Retreats** — "Deep experiential immersion in ancestral contemplative
   traditions and the work of integration." → `/retreats`
2. **Online Living Wisdom Courses** — "Bring Primordial Breathwork, Qigong, Remembrance
   and contemplative practice into everyday life." → `/online-courses`
3. **1-on-1 Mentorship & Dreamwork** — "Individual guidance for people seeking sustained
   integration, self-understanding and support through significant life transitions."
   → `/mentorship`
4. **Support Indigenous & Conservation Initiatives** — "Participate directly in the
   Yahua and Q'ero initiatives, conservation and cultural preservation." → `/initiatives`

Keep everything above (legitimacy block) and below (Impact, book, tribes) as-is.
Give the Impact section `id="impact"` for the nav anchor.

### 1.3 /online-courses gateway (OnlineCourses.dc.html)

Insert a crawlable course-card section between the hero and the Retreat Guru iframe
(keep the iframe — it is the live booking path). One card per course, 100–200 words,
"Explore the Course →" to the existing enrollment destination. Course list **pending
Roman #1**; build the section with the four ChatGPT-session courses and adjust:

- Primordial Breathwork · Alchemy of Immortality Qigong — Andean Art of Being ·
  Ancestral Remembrance · Practical Alchemy Series

Note for the catalogue conversation: the existing **"Embody True Nature Evolutionary
Healing Home Study Course"** section on this page ("Discover the blueprint encoded in
ancestral wisdom lineages…", Coming Soon + early-bird JotForm) is plausibly the same
thing as Roman's favourite **"Your Evolutionary Blueprint"** — the old homepage promised
"Breathwork · Qi Gong · Evolutionary Blueprint". Resolve the naming with Roman, don't
duplicate it as a fifth card by accident.

### 1.4 /mentorship — new page

- Title: **Individual Mentorship & Dreamwork with Roman Hanis**. NOT "Life Coaching".
- Strands: Amazonian Dreamwork · Jungian depth psychology · Contemplative inquiry ·
  Life integration · Shadow work · Embodied practices · Relationship with nature ·
  Purpose and major life transitions.
- Required disclaimer, verbatim: "This work is not psychotherapy or medical treatment
  and is not intended to replace licensed mental-health or medical care."
- CTA: **Book a Connection Call** → reuse Team's
  `mailto:roman@paititi-institute.org?subject=15 min connection call` for now; upgrade
  to a booking/intake form later.
- Build as a normal `.dc.html` page on the fluid engine; add to `_redirects`,
  sitemap, header.

### 1.5 /retreats gateway (Retreats.dc.html)

Keep the Himalayan Pilgrimage block and the Retreat Guru iframe. Add:

- Framing copy at top (endorsed draft, usable): "Retreats at Paititi are not an escape
  from ordinary life. They are immersive spaces for remembering what becomes possible
  when ancestral practice, contemplative inquiry, nature and community are brought
  together, and for learning to carry that remembrance back into relationship, family,
  work and service."
- **"Where Your Participation Goes"** reciprocity section (endorsed draft, usable):
  "Paititi Institute's transformational programs form part of a larger nonprofit
  ecosystem. Revenue from retreats, courses and educational programs helps sustain the
  Institute's conservation, Indigenous education and community initiatives. Participants
  therefore enter a reciprocal relationship: receiving practices preserved through
  living wisdom traditions while helping those traditions, communities and landscapes
  continue into future generations." The model itself is reciprocal — not "buy a
  retreat and we donate". (The Initiatives page's "in-breath/out-breath" retreats
  accordion says the same thing; echo, don't contradict.)
- Himalayan Pilgrimage price: **pending Roman #2** (notes said $2,500–3,900; page
  currently shows dates Oct 17–31 2026, no price).

### 1.6 Content fixes

- AboutUs.dc.html:185 — rewrite Earth Stewardship accordion: "4000 acre nature
  reserve" → "1,516-hectare biocultural reserve"; fix "Permacutlure" → "Permaculture".
- DiscoverPaititi.dc.html:182 — same 1,516 ha fix.
- Blog post "can't-blame-the-chaos" also says "4,000 acre" — it is Roman's authored
  article; leave unless Roman wants it touched.
- BeyondAyahuasca.dc.html:133 — replace "A portion of the book's proceeds will directly
  support the building and operation of the cultural heritage center" with the standard
  royalties sentence (confirmed by Roman's 11 Aug message — see "Answered" above).
- Team.dc.html:83 — align the bio's "with proceeds directly supporting" phrasing with
  the same commitment.
- Initiatives.dc.html:150 — write real copy for "Land — pantry and classroom" (pantry:
  food forests/seed nurseries; classroom: the reserve as living curriculum — source
  from the live-vision mindmap PDF or Roman), replacing the duplicated School paragraph.
- Team.dc.html — meta title "Team 1 | …" → "Team | Paititi Institute"; fix "elders of
  the and Yahua tribe"; consider unbolding the bio prose.

### 1.7 Launch checklist (technical)

- **Remove `noindex` from all pages except** Cart, OrderConfirmed, the two
  DistanceHealing payment pages, and store checkout paths. This is the single most
  important launch step — everything is noindexed today.
- Add `404.html` (server.js:169 already looks for it; add to `_redirects`/worker
  behaviour for Cloudflare) routing people to Programs/Initiatives.
- `_redirects`: add `/courses`, `/journal`, and the row-11 ancient paths.
- sitemap.xml: add `/mentorship`; resubmit in GSC after DNS switch; sort owner-level
  GSC access with the migration.
- Unique meta title/description for the touched pages (Home cards section doesn't
  change Home's; /mentorship needs new; OnlineCourses description could name the
  actual courses).
- Alt text on new/touched imagery.
- Post-launch crawl: no internal links to old paths, no leftover noindex, DH tab
  anchors resolve.
- Publishing habit note: blog/Journal posts go website-first, Substack after a delay
  with a canonical link back.

## Phase 2 — right after migration

- Ad Grant campaigns → landing families: breathwork → `/online-courses` (course page
  when it exists) · dreamwork/mentorship → `/mentorship` · retreats → `/retreats` ·
  conservation/Indigenous education → `/initiatives`. Search-only, activity + CTR
  minimums, no single-word generics.
- How Paititi Works page (Practice → Transformation → Reciprocity → Service → Living
  Wisdom ↺). Why Paititi page (honest differentiation, no competitor naming).
- Individual course pages under `/online-courses/…`.
- Mentorship/DH intake forms replacing the mailto; distancehealing@ inbox decision.
- Initiatives subpages if the anchor approach feels thin.

## Phase 3 — ongoing

15 cornerstone evergreen articles, 2–3/month, Roman writes or reviews; facts about the
nations, reserve, and practices come from Roman or verified sources, never invented.
List in the working notes. Never blocks anything.

## The three remaining Roman blockers (one confirm-or-correct batch, ~10 min)

1. **Course catalogue + order** — the four courses from his session (Primordial
   Breathwork · Alchemy of Immortality Qigong · Ancestral Remembrance · Practical
   Alchemy Series) vs the old homepage promise of "Breathwork · Qi Gong · Evolutionary
   Blueprint"; is "Embody True Nature Home Study Course" the same as "Your Evolutionary
   Blueprint"? What order? (Note from his transcript: the Beyond Ayahuasca page already
   describes the Practical Alchemy Series better than the courses page — reuse that
   copy for its card.)
2. **Himalayan Pilgrimage** — Oct 17–31 2026 is on the page; price ($2,500–3,900?) and
   whether to show it.
3. ~~**Distance Healing placement**~~ — **decided (12 Aug): Programs dropdown next
   to Mentorship**, which is what's built. Still open from this item: who receives
   distancehealing@paititi-institute.org; keep the separate inbox?

Everything else in Phase 1 is buildable without him.
