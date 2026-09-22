# FAQ — draft for Roman

**Status: draft. Nothing here is on the site.** Not published (`docs/` is in
`.assetsignore`).

Why this exists: an answer engine — ChatGPT, Claude, Perplexity, Google's AI
answers — quotes most readily from a plain question followed by a direct answer,
and the site has no such section anywhere. See the AI search notes in
`docs/seo.md`.

**How to read this file.** Every answer below is either

- **[SOURCED]** — assembled from wording already public on the site, with the
  page named. Roman's job here is to correct the emphasis, not to supply facts.
- **[NEEDS ROMAN]** — deliberately left unwritten. These are questions where a
  wrong answer is a medical, legal or financial claim made in Paititi's name,
  and where the site currently says nothing I could build on. I have written
  what is needed and why rather than a draft to react to, because a plausible
  draft of a legal answer is worse than a blank: it is the thing that gets
  approved quickly.

When answers are settled, they go on the site as a real page or section and
`tools/apply_schema.py` gains `FAQPage` markup for them — that part is small.
The writing is the work.

---

## The organisation

### What is Paititi Institute?

**[SOURCED — /about-us, /initiatives]**

Paititi Institute is a nonprofit working alongside Indigenous communities in the
Peruvian Amazon and Andes. Founded in 2010 by Roman Hanis, it supports
community-led education, healthcare, cultural preservation and ecological
stewardship, and holds a 1,516-hectare biocultural reserve between the two
regions. Its programmes — retreats, courses and mentorship — are part of the
same body of work rather than a separate business alongside it.

### Is Paititi a registered nonprofit, and is my donation tax-deductible?

**[SOURCED — /about-us]**

Paititi Institute is a registered Peruvian nonprofit (NGO), accredited by Peru's
Agency for International Cooperation (APCI). In the United States, donations are
tax-deductible through fiscal sponsorship by Empowerment WORKS, Inc., which
holds the 501(c)(3) determination.

> **Note, and please keep this distinction in the published wording:** the
> 501(c)(3) and its EIN belong to Empowerment WORKS, not to Paititi. Saying
> "Paititi Institute is a 501(c)(3)" without the sponsorship is inaccurate, and
> it is exactly the sentence a donor's accountant will check. This is also why
> the structured data carries no EIN.

### Where does the money go?

**[SOURCED — the endorsed "Where Your Participation Goes" text in build-spec.md
§1.5, reused verbatim]**

Paititi Institute's transformational programs form part of a larger nonprofit
ecosystem. Revenue from retreats, courses and educational programs helps sustain
the Institute's conservation, Indigenous education and community initiatives.
Participants therefore enter a reciprocal relationship: receiving practices
preserved through living wisdom traditions while helping those traditions,
communities and landscapes continue into future generations.

### Can I give to a specific initiative?

**[SOURCED — /support]**

Yes. Two campaigns are open now — the Yahua Ancestral School in the Amazon and
the Q'ero Ancestral School in the Andes — each with its own form on /support.
Campaigns for the Paititi Biocultural Reserve and for the Seed of the Heart
circles are being prepared.

---

## Retreats

### Where do the retreats take place?

**[SOURCED — /retreats/amazon-16-day-embodying-true-nature-immersion]**

The main immersions are held in the Peruvian Amazon, about an hour outside
Iquitos and reached by boat. Paititi also runs shorter workshops and talks in
California, and a Himalayan Pilgrimage through Nepal.

### What actually happens during a retreat?

**[SOURCED — the same page]**

The 16-day Embodying True Nature Immersion is the most comprehensive of them.
Days combine Remembrance, Indigenous-based Primordial Breathwork, Indigenous and
Jungian transpersonal Dreamwork, Symptomatic Dance and Sacred Geometry, Daoist
and Andean Qigong, meditation, medicinal plants, sacred plant ceremonies,
movement, creative expression, self-inquiry and integration. The emphasis falls
on integration: the retreat is concerned with how a recognition becomes
embodied, so that it continues through ordinary relationships, work and
responsibilities rather than remaining an extraordinary experience in the
rainforest.

> Roman — a genuine day-by-day outline would be the single most quoted thing on
> the site. "Morning: … / afternoon: … / ceremony nights: …" Six or seven lines.
> People searching are trying to picture it, and no page currently lets them.

### Which plant traditions do you work with?

**[SOURCED — the same page]**

Ayahuasca from the Amazon, San Pedro (Huachuma) and the sacred relationship with
Coca from the Andes, each approached within its own cultural and cosmological
context. Within the Indigenous traditions these come from, the ceremonies belong
to a much larger process involving relationship with nature, cosmovision,
initiation, ancestral practice, community, and integration into everyday life.

### What does a retreat cost, and what is included?

**[SOURCED — the same page. Figures are for the Dec 2026 immersion and will date.]**

The 16-day immersion is a sliding scale of $2,333 to $2,777 USD. That covers
accommodation in the rainforest — shared rooms, with private rooms when
available — meals suited to the retreat and the plant work, and the full
programme. Accepted participants also receive preparation guidance and lifelong
access to Paititi's self-paced online course, Your Evolutionary Blueprint.

> Two gaps: what the price does **not** include (flights, the Iquitos transfer,
> insurance, visas?) and the **cancellation and refund policy**. Both are the
> first things a careful person looks for. Retreat Guru may already state them —
> if so, we should repeat them here rather than send people off-site.

### How do I join?

**[SOURCED — the same page]**

Every retreat requires an application and a health screening, and booking runs
through Retreat Guru from each programme's page.

---

## Suitability and safety

This section matters more than the rest. It is also where the site currently
says least.

### Is this therapy or medical treatment?

**[SOURCED — required disclaimer, build-spec.md §1.4, verbatim]**

This work is not psychotherapy or medical treatment and is not intended to
replace licensed mental-health or medical care.

### Who should not attend? What conditions or medications rule someone out?

**[NEEDS ROMAN — not drafted, deliberately]**

The site says "application and health screening required" and stops there. It
never says what the screening looks for.

I am not writing this one. Any specific list — SSRIs and MAOIs, cardiac
conditions, a personal or family history of psychosis, pregnancy — is a clinical
claim published in Paititi's name, and the honest version has to come from
whoever actually conducts the screening. A confident-sounding paragraph written
from general knowledge is the worst possible outcome here, because it reads as
authoritative and gets approved without anyone checking it.

What is needed: the real screening criteria as the facilitators apply them, in
whatever form they exist already, plus a clear statement of who makes the final
call. Even "we review every application individually with a clinician, and these
are the things we always ask about" is far better than silence, and it is
truthful.

### Is ayahuasca legal in Peru?

**[NEEDS ROMAN — not drafted, deliberately]**

This is one of the most common searches in the field and the site does not
address it. It is also a legal question about a jurisdiction Paititi operates in
and I do not, so it should be answered by Paititi — ideally checked by Roland
Huilcanina Huarhua, the Institute's Peruvian counsel, who is already named on
/about-us.

Worth answering in the same breath: what that means for a visitor travelling
home, which is the part people are really asking about and which is *not* the
same question.

---

## Other ways to take part

### Do I have to travel to Peru?

**[SOURCED — /online-courses, /mentorship, /distance-healing, /retreats]**

No. There are four self-paced online courses, one-to-one Individual Mentorship
and Dreamwork with Roman Hanis, a three-month Distance Healing programme, and
workshops and talks held in California.

### What are the online courses?

**[SOURCED — /online-courses]**

Four self-paced home-study courses: Your Evolutionary Blueprint, Primordial
Breathwork, Alchemy of Immortality Qigong — Andean Art of Being, and the
Practical Alchemy Series that accompanies the book. Each now has a page of its
own with full details and enrolment.

---

## The initiatives

### Who are the Yahua and the Q'ero, and what is Paititi's relationship with them?

**[PART SOURCED — /initiatives/yagua-…, /initiatives/qero-…]**

The Yahua are an Amazonian people; the Q'ero are a Quechua-speaking nation of
the high Andes. Paititi has worked alongside Indigenous nations for over two
decades, and the current work with both is the Ancestral School: the first
maloca of the Yahua school is complete, and the same model is now extending to
the Q'ero — a space where elders and children remain in daily continuity, and
where language, cosmology, land stewardship and rites of passage are transmitted
as lived responsibility rather than performance.

> Roman — the relationship itself is the part I would not put words to. Whether
> Paititi describes itself as partner, supporter, invited guest or something
> else is yours, and it is the sentence a journalist or a grant officer will
> quote. One clear line on how the collaboration was formed and who leads it.

### What is the Paititi Biocultural Reserve?

**[SOURCED — /initiatives/paititi-biocultural-reserve]**

1,516 hectares in the Mapacho Valley, where the high Peruvian Andes give way to
cloud forest. It spans three ecological horizons from 1,800m to 3,500m, holds
dozens of springs, and acts as a buffer to the Manu National Park Reserve. Its
title was affirmed in 2026.

---

## Where this should live when it is settled

A dedicated `/faq` page, with the answers grouped as above, and the questions as
real headings so each one can be linked to and quoted on its own. The Spanish
twin at `/es/preguntas-frecuentes` is part of the job, not a follow-up.

The two `[NEEDS ROMAN]` answers should not hold up the rest. Publishing twelve
good answers and adding safety and legality when they are ready is better than
publishing nothing for another month — but they should not be quietly dropped
either, because they are two of the three questions people most want answered.
