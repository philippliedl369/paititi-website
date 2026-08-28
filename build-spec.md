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

## Post-migration review, 25 Aug 2026 (Roman's AI, second pass)

A review of the migrated site as Google was recrawling it. Checked line by line
against the repo. Most of it describes the **old Squarespace crawl**, not this
build — the reviewer was reading an index that still held pre-migration pages.
Recorded here so the same list does not get re-litigated.

**Real, and fixed in this pass:**

- `Home.dc.html` "Supporting the Yahua and Q'ero tribes" still said *"100% of
  proceeds will be donated"* — the one place on the site that had not been moved
  to the royalties commitment, and it sat directly under the book block, so it
  read as a claim about book proceeds. Now the standard sentence. (The Impact
  list higher up the same page already said "100% of the author's royalties",
  so the page contradicted itself.)
- `OnlineCourses.dc.html` hero: "Our transformative courses … **invites** you"
  → "invite you".
- `Privacy.dc.html`: four sentences run together with no space after the full
  stop ("…anyone else.We collect…"), inherited from the Squarespace copy.
- `BlogPost-cant-blame-the-chaos…`: a photo caption linked
  `paititi-institute.org/wp-content/uploads/2019/09/…jpg` — a WordPress-era path
  this site 404s. Credit kept as text, link dropped.

**Already built — do not re-do:**

- *"Add Individual Mentorship & Dreamwork as a visible pathway"* — the homepage
  carousel is gone; "Ways to Walk With Us" has been four cards since §1.2, one
  of them `/mentorship`.
- *"Strengthen the Online Courses hub"* — §1.3. Four crawlable cards, 100–200
  words each, ahead of the Retreat Guru iframe.
- *"Embody True Nature retreats weaves"* and *"Learn how your support…" run into
  the previous sentence* — neither string exists in this repo. Both are old
  Squarespace homepage copy that the rebuild replaced.
- *"Dedicated landing pages for Yahua and Q'ero"* — both exist and are in the
  sitemap.
- *"Make the timeline, fiscal sponsorship, APCI and impact visible early on
  About"* — `AboutUs.dc.html:157` (501(c)(3)/EIN/APCI facts) and `:172` (2014
  timeline entry) are above the philosophical material, not below it.

**Legacy `/wp-content/uploads/…` PDFs (the reviewer's "highest-value technical
cleanup"): nothing to do.** Those files are not in this repo, and
`wrangler.jsonc` sets `not_found_handling: "404-page"`, so every one of them
already returns a hard 404 — verified live on three paths, 25 Aug. Google drops
them on recrawl; there is no de-indexing step to perform. Do not add redirects
for them: 301-ing an outdated work-study PDF onto a current page would launder
the stale content into a live URL instead of retiring it.

**Still open (Phase 2, unchanged by this review):** separate landing pages for
the Biocultural Reserve and Community Health (anchors today), individual course
pages, and the evergreen article set — already §§Phase 2/3 below. The reviewer's
"what is a biocultural reserve / Indigenous-led conservation / Amazonian
dreamwork" question-shaped titles are a good seed list for Phase 3.

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
"Explore the Course →" to the existing enrollment destination.

**Settled 25 Aug** by Roman's post-migration review. The catalogue is the four
programs Retreat Guru actually sells, flagship first:

- Your Evolutionary Blueprint · Primordial Breathwork · Alchemy of Immortality
  Qigong — Andean Art of Being · Practical Alchemy Series

Two corrections that came with it. The **"Embody True Nature Evolutionary Healing
Home Study Course"** section was *not* the same thing as Your Evolutionary Blueprint —
Roman reads it as "an old message from the Paititidistancehealing website" about a
course that never shipped, so the Coming Soon copy and its early-bird JotForm are
gone. And **Ancestral Remembrance** has no enrollment page of its own: its card
pointed at the Practical Alchemy Series program, the same destination as the
Practical Alchemy card, which Roman flagged as two cards leading to one place. It is
now described inside the Practical Alchemy card instead of holding a card of its own.
If Roman wants it sold separately, that starts with a new Retreat Guru program.

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

### /press-media rebuilt (25 Aug)

The page was a Squarespace transcription: one article thumbnail on a hero, reachable
only from the footer. It is now the site's media home — films, then coverage, then a
journalist block (contact, what we can provide, fast facts) — and sits in the nav
under About, in both language trees (`/es/prensa` is wired in `_redirects` and linked
from the Spanish header and footer; `PressMedia.es.dc.html` was written on 25 Aug
with the rest of the Spanish tree).

It exists mostly because **the current documentary had no signposted home**. *Ayahuasca:
The Medicine of Awakening* was embedded halfway down `/beyond-ayahuasca` and
`/initiatives/yagua-…`, and carded on `/discoverpaititi`, which is not in the nav —
so from the front door it was unfindable. It now plays at the top of `/press-media`.
(Its title is "…Medicine **of** Awakening"; `/discoverpaititi` said "for" and is fixed.)

What is on the page is everything that could be verified against a live source.

**Rebuilt from Roman's press archive (26 Aug).** The coverage list went from four items
to 28, chronological, newest first, drawn from the archive PDF he sent. Screenings,
directory listings and the Reality Sandwich reprints were left out on purpose — a
screening is not coverage and a directory entry is not a publication.

**Restructured into five sections (27 Aug).** The page now carries the same sticky
section nav as `/distance-healing` and `/initiatives` (`.pm-subnav`, the identical
component and script, `--pm-nav-top` following the retracting header). It replaced
three jump pills in the hero that named only three of the sections and scrolled away
after the first screen.

The five sections, alternating lilac/white down to the plum journalist band:

1. **Films** (`#films`) — films made *about* this work. *Ayahuasca: The Medicine of
   Awakening* (embedded feature), *An Ancestral School for the Yahua Tribe is Born*
   (short), *The Sacred Science* (2010).
2. **On camera** (`#on-camera`) — Roman in someone else's conversation: six players,
   three filmed interviews, a live environmental news stream, an online class and a
   conference talk. Was a strip buried inside Coverage; it is a section of its own now
   and sits beside Films, because both are things you press play on and the line
   between them is who made the thing, not the format.
3. **In the press** (`#coverage`) — the 28-row chronological list. Rows for filmed
   pieces point *up* to their player in On camera; the print row points *down* to its
   scan.
4. **In print** (`#print`) — scans, each beside a full translation on the English side
   where the original is not in English. Was also a strip inside Coverage.
5. **Media enquiries** (`#enquiries`) — contact, what we can provide, fast facts.

Spanish mirrors all of it (`Películas · En cámara · En la prensa · En papel ·
Consultas de prensa`); its hero also picked up the top-anchored crop and the ≤640
`contain` fallback the English hero already had.

**Open, needs Roman.** Nothing on a press page may be invented, so these are asks, not
build work: (a) further newspaper and magazine clippings — scans go in `assets/press/`,
the markup template is in a comment in the page; (b) any coverage still missing from
the list; (c) confirmation that `info@` is the right inbox for media enquiries.

## The Living Wisdom School (opened 27 Aug 2026)

Source: *Living Wisdom School — Updated Working Overview for Roman, Kelly & Joseph*,
Paititi Institute, August 2026 (PDF, internal). It describes an umbrella educational
ecosystem — the Evolutionary Blueprint as its map, lineage streams, a four-rite
passage path, layered online learning, physical hubs, a council, membership stages —
with a development sequence that puts **public launch in 2027** and 2026 as
"Foundation and Story". Its §18 says the building of the school is itself the story,
which is what licenses anything appearing on the site now.

So this pass seeds the idea into pages that already exist. It does **not** build the
school as a product.

### The naming collision — decide before anything else ships

"Living Wisdom" is now on the site in three senses, and two of them predate the doc:

| Sense | Where | What it means |
|---|---|---|
| Living Wisdom **Center** | `SiteHeader.dc.html:172` (announcement bar), `InitiativeYagua.dc.html:147` + its meta description | a **building** at the Yahua site, and the current donation ask |
| Living Wisdom **Courses** | `OnlineCourses.dc.html:137`, `Home.dc.html:192`, `DiscoverPaititi.dc.html:379` | the four Retreat Guru courses |
| Living Wisdom **School** | the doc; now the new copy below | the umbrella body containing retreats, courses, mentorship |

A donor who reads the announcement bar and then a school page cannot tell which one
their money builds. The new copy mitigates this by defining the Center and the School
against each other in the one place a reader meets both (`/initiatives#culture-learning`),
but that is a patch, not the decision. Spanish carries the identical collision:
*Centro de Sabiduría Viva* / *Cursos de Sabiduría Viva* / *Escuela de Sabiduría Viva*.

**Proposed, pending Roman:** Center stays the Yahua building; School is the umbrella;
"Living Wisdom Courses" as a section heading retires to plain "Courses" once the
school has a page of its own. Not applied — it touches six files in two languages.

### The Evolutionary Blueprint has two versions

The doc's Blueprint is **seven** stages: Conditioning → The Call → Descent →
Remembrance → Integration → Reciprocity → Service. The Blueprint course sold on
`OnlineCourses.dc.html:150` is **five** chapters ("the call to evolve, crossing the
line of no return, remembering the infinite, finding the way through the patterns of
evolution, emerging from the dark night of the soul"). Same framework, earlier
version — consistent with the doc's own 2027 line, "refine and relaunch the
Evolutionary Blueprint". The additions at the front (Conditioning) and back
(Reciprocity, Service) are exactly the turn toward the nonprofit work.

Consequence: **no page may state a stage count until Roman settles it**, or the school
copy and the course card contradict each other. Nothing shipped here names either.

### Built, 27 Aug — six files, both language trees

1. `/initiatives#culture-learning` — new "Two Schools, One Movement" block
   (`Initiatives.dc.html`, `Initiatives.es.dc.html`). The chapter previously held only
   the inward half (Yahua school, e-campus); this is the doc's §13 reciprocal
   architecture, and the only place both "Living Wisdom" senses are defined together.
   Grid: new block at rows 33–47 (EN) / 33–48 (ES), video pushed down, `--pt-rows`
   44 → 60 (EN) / 61 (ES). Measured, not guessed.
2. `/initiatives#living-system` — sixth flow line, "Ancestral schools ↔ Living Wisdom
   School". `--pt-rows` 30 → 36 (EN) / 37 (ES).
3. `/online-courses` — one paragraph under the catalogue heading naming these four as
   the school's first materials, linking to the Initiatives chapter.
4. `/retreats` — **The Rites of Passage Path**, four cards inside the existing framing
   section (so the framing → Himalayan wave rhythm is untouched), plus new section ids
   `#amazon-immersion` and `#himalayan-pilgrimage`, plus a closing note on §9 ("the
   school happens between the rites").

The rites section only works because two of the four rites are *already running*:
Rite I is the Amazon 16-day immersion further down the page, Rite IV is the Himalayan
Pilgrimage. Rites II and III carry explicit "In development" / "A longer horizon"
markers and must never become bookable-looking without a real program behind them.

**One editorial decision is load-bearing there.** The doc frames Rite IV as being for
people "who have established greater grounding through practice and earlier
experiences" — a prerequisite. The Himalayan Pilgrimage on the same page takes open
registration with no prerequisite, so the copy says the ordering "describes how they
relate to one another rather than a set of requirements". If Roman wants the
prerequisites to be real, that sentence changes first, and registration has to change
with it.

Verified: no grid overlap and no horizontal scroll at 1440, 1190 and 390px in both
trees; `apply_hreflang.py --check` in step; all six new internal links resolve.

### Deliberately not built

- **No `/living-wisdom-school` page.** Waiting on the naming decision and on how much
  of the 2027 sequence Roman wants public. When it is built it follows the
  `/initiatives` pattern (hero + sticky chapter subnav + chapters) and needs a Spanish
  twin, `_redirects`, `sitemap.xml` and `tools/i18n_pairs.json`.
- **No nav entry.** The school is a *parent* of Programs, not a sibling, so promoting
  it before the page exists would restructure the header around nothing. Intended
  placement: first item in Programs ▾, above the four programs.
- **No dates on the site.** The 2027 launch and the 2028–2030 sequence stay internal;
  published roadmaps age badly and this one has no committed resourcing.
- **Kelly and Joseph are not named.** The Team page is Roman-only by his own 11 Aug
  decision, and there are no bios, photos or consent. The copy says nothing about who
  staffs the school.
- **No named elders or teachers.** §19 says the council should grow through real
  relationships rather than be assembled for appearance; a website faculty grid is the
  same mistake in another form. No individuals, no consent, nothing published.
- **No membership tiers, hubs or Rite III specifics.** Participant/Practitioner/
  Steward/Mentor, the Peru / Bay Area / Korea / Thailand / Nepal hub list, and the deep
  rainforest initiation are all speculative; only Rite III appears at all, marked as a
  horizon with its safety preconditions stated.
- **The doc itself is not published.** It is addressed to three named people and reads
  as internal. A public-facing version would be a separate artifact, in the manner of
  the Living Vision mind-map PDF.

### Open — needs Roman

1. **The naming decision above.** Blocks the dedicated page.
2. **Blueprint stage count** — 7 stages, or keep the course's 5? Blocks any page that
   describes the framework, and decides whether the course card gets rewritten.
3. **Rite prerequisites** — map or gate? Decides whether the Himalayan registration
   stays open to anyone.
4. **How public is the roadmap?** Whether "2027" may appear on the site at all.
5. **Kelly and Joseph** — named publicly as part of this, or not yet? If yes, bios,
   photos and their own sign-off, and it reopens the Roman-only Team page decision.
6. **Announcement bar** — it currently sells the Yahua Center. Does it stay that way
   through the school's introduction, or does the school get its own moment?
7. **Rite II (Andes)** — is the horseback pilgrimage real enough to name as in
   development, or should it come off the page until there is a date?

### Further work, in order

1. Roman answers 1–3 above (the rest can wait).
2. `/living-wisdom-school` — vision page on the `/initiatives` pattern; chapters from
   §§1–5, 8–9, 13, 15, 18. Both languages, plus the four registration files.
3. Nav entry in Programs ▾; re-point the four grafted links at the new page.
4. Journal post — §18 is a content brief, "why we are building a school", website
   first and Substack after with a canonical link back. Roman writes or reviews.
   It also seeds the Phase 3 evergreen set, which is still empty.
5. Only after all of that: anything resembling enrollment, and only once Retreat Guru
   has a program behind it.

## Elders & children, the Q'ero school, and reachable donations (27 Aug 2026)

Philipp's batch of 27 Aug, all built in both language trees:

1. **Third initiative page** — `/initiatives/uniting-elders-and-children`
   (`InitiativeElders.dc.html`, ES `/es/iniciativas/uniendo-mayores-y-ninos`). The Seed of
   the Heart initiative, sitting beside the Yahua and Q'ero pages: hero, the mini-documentary
   (YouTube `tPmqXtte86M`, Nov 2025) with the prophecy framing, three "where the seed is
   planted" cards (Yahua school, Q'ero school, the travelling workshops), a plum support
   section with both Zeffy campaigns, and a pager. Built in flow like `/discoverpaititi` —
   no fluid grid, nothing to measure. Every fact comes from the Institute's own published
   copy: the video description (workshop reach — Amazon, Andes, Mexico, Oregon, Colorado,
   New Mexico; collaborators in South America, US, Nepal, India, Africa, Australia) and the
   existing site (children's book, royalties line). Nothing invented. Wired into the
   Initiatives ▾ dropdown and mobile menu (both headers), `_redirects`, `tools/i18n_pairs.json`,
   hreflang blocks and `sitemap.xml` via `apply_hreflang.py`.
2. **The Q'ero page is no longer a 2021 COVID page.** `InitiativeQero.dc.html` keeps its URL
   (`/initiatives/qero-nation-emergency-food-supply` — the slug is what's indexed and
   linked; changing it buys nothing) but is retitled *An Ancestral School for the Q'ero
   Nation*. New first section, in flow: the Feb 2026 short film (`UswFoaw2xPc`), the lead
   from its description, the "what the school will support" list and the "how you can take
   part" list from the Zeffy campaign page, the Q'ero elders photo, and the Zeffy link. The
   2021 journey section is untouched below it, its first paragraph now opening "How it
   began." — the title was left alone because a two-line title in that cell overlaps the
   video (the one-line title already nearly touches it on the live replica).
   **The old donation panel was dead**: it posted to `/api/checkout`, which `api.js` answers
   with "unavailable" because `STRIPE_SECRET_KEY` is not set (Stripe went with the store).
   It is now the Q'ero campaign's Zeffy embed
   (`developing-ancestral-schools-for-the-qero-nation-in-the-peruvian-highlands`), section
   id `#donate`, rows 13 → 16 for the 541px iframe; the DC component script is gone with it.
   Hero gained a "Donate to the Q'ero school" button (rows 14–16). Pager now has Previous
   (Yahua) *and* Next (Elders & children).
3. **Donations are reachable.** The header Support/Apoyar button now lands on
   `…yagua-…#donate`, and on the Yahua page that anchor is a new lilac strip *directly under
   the hero* — copy left, the Zeffy embed right, in flow — instead of the form that used to
   sit at row 61 of a 75-row section under two videos and the whole appeal. The appeal
   section (`#expanding`) lost its duplicate iframe + note, the three `&nbsp;` paragraphs
   went, and it ends on a "Donate through Zeffy" button back up to `#donate`; rows 75 → 64,
   prose cell 31–61 (ink 986px in a 1093px cell at 1440, measured). The strip also
   cross-links the Q'ero campaign, and the Q'ero donate section links back.
4. **The elders video is back on `/discoverpaititi`** — a white section between "Choose
   where to begin" and the name section (`#seed-of-the-heart`): kicker, title, one
   paragraph, the embed, and two links (initiative page, `#donate`). It was never in
   `DiscoverPaititi.dc.html` in git; it was on the Yahua page and `/initiatives` only.
5. **`/press-media` Films** has a fourth card for the mini-documentary, placed second (the
   Apr 2026 documentary is still the newest); `.pm-grid` is three across now so there is no
   orphan. The film lead says "Four films". Lesson recorded: a `.pm-card` is an `<a>`, so no
   links inside its copy — the parser closes the card at a nested anchor and the grid gets
   four items.
6. `/initiatives`: the Yahua paragraph's "in time, to the Q'ero" became "now extending to
   the Andes … in development" with a link; the Seed of the Heart embed gained a caption
   row linking the new page (`#culture-learning` rows 60 → 63 EN / 61 → 64 ES); Walk With
   Us is three cards across (`.in-grid` 3 columns, photos 432 → 300px, section rows 22 →
   19), the Q'ero card retitled and re-photographed (the Q'ero elders at the stone hut
   instead of the COVID aid graphic).

Verified over CDP at 1440, 1190 and 390 on every touched page in both languages: no
horizontal overflow, no cell spill; the only sibling overlaps reported are the two the
live replica already had (Q'ero journey title/video, the Yahua flower graphic).

Open for Roman, non-blocking: (a) the Q'ero campaign's own photos — the page reuses the
Nov 2025 Home/About shot; (b) whether the Seed of the Heart *book* should get a card of
its own once it is published; (c) the announcement bar still sells only the Yahua Center
now that two campaigns are open.

## Phase 3 — ongoing

15 cornerstone evergreen articles, 2–3/month, Roman writes or reviews; facts about the
nations, reserve, and practices come from Roman or verified sources, never invented.
List in the working notes. Never blocks anything.

## The three remaining Roman blockers (one confirm-or-correct batch, ~10 min)

1. ~~**Course catalogue + order**~~ — **answered 25 Aug**: Your Evolutionary Blueprint
   is the flagship and leads; "Embody True Nature Home Study Course" was a stale
   Distance Healing promo, not the same course, and is removed; Ancestral Remembrance
   folds into the Practical Alchemy Series card. Built — see §1.3.
2. **Himalayan Pilgrimage** — Oct 17–31 2026 is on the page; price ($2,500–3,900?) and
   whether to show it.
3. ~~**Distance Healing placement**~~ — **decided (12 Aug): Programs dropdown next
   to Mentorship**, which is what's built. Still open from this item: who receives
   distancehealing@paititi-institute.org; keep the separate inbox?

Everything else in Phase 1 is buildable without him.

A second, separate batch is now open on the Living Wisdom School — naming, the
Blueprint stage count and whether the rites are a map or a gate are the three that
block further build. See **The Living Wisdom School** above; the rest of that list can
wait, and nothing already shipped depends on the answers.

## Roman-only: the Retreat Guru website field

Retreat Guru builds every link back to "our website" from one field in its admin, as
`<website>/?programs=1&program=<id>` — the deep-link shape the RBG Connect widget
answers. Through the migration that field still read `paititi-institute.squarespace.com`,
so all five program links on his teacher page
(`paititi-institute.secure.retreat.guru/teacher/roman-hanis/`) and on the centre's
programs list led back to the old Squarespace site, which is still serving. Nobody on
this side can change it: it needs the Retreat Guru login.

Setting that field to `https://paititi-institute.org` is the whole fix.
`retreatguru-deeplink.js` (loaded on Home, Retreats and Online Courses) maps each
program id onto the page that presents it, so the links land on the right course
rather than dumping everyone on the homepage. Program ids as of 25 Aug: 614 Your
Evolutionary Blueprint · 632 Alchemy of Immortality Qigong · 638 Primordial
Breathwork · 997 Practical Alchemy Series · 1046 Amazon 16-day Immersion. Re-read
them from the teacher page if a program is added or replaced.
