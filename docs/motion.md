# Motion — workflow, doctrine, and primitives

Extracted from a production site's motion program (inspired by motionsites.io-class
work). The brand-specific concepts were left behind; what carries over is the
**working method**, the **rules that made the motion read as substance**, and the
**battle-tested CSS primitives**. Use this doc as the template for the Meristem
motion program: every ⬜ is a decision to work out for this brand.

---

## The doctrine (adapt, don't skip)

The one rule the original program converged on, from six independent creative lenses:

> **Motion must carry information, run once, and end at rest.**

And the brand-defining corollary: decide **what motion resolves *to***. The original
brand resolved every set piece to a *marked problem* (its business was finding where
work breaks); competitors animate toward happy resolutions or loop forever, which is
exactly why an ending with meaning reads as signal.

- ⬜ **What does motion resolve to for Meristem?** (One sentence. Every set piece
  ends on it.)
- **Ink is never retracted** — reveals draw in and fade out; they never rewind.
- **No loops.** No spinners, no infinite marquees of attention, no count-up numbers
  (the SaaS cliché). A number only gets emphasis if it can carry a receipt.
- **Reduced motion / no JS = the resting design.** Every animated element's final
  frame *is* the designed state; `prefers-reduced-motion` and script-off users simply
  get the page at rest. Hiding CSS is injected from JS so its absence is the fallback.
- **Motion budget** (publishable, enforceable): at most one set piece per page,
  under ~4s of motion total, everything ends at rest. Some pages are **deliberately
  dead still** — that stillness is what makes the moving moments legible.
  Optional CI check: grep for `animation-iteration-count: infinite`.

## The workflow (what actually produced good results)

1. **Multi-lens brainstorm.** Several distinct creative lenses (6 worked well)
   each produce concepts independently — aim for volume (23 first pass).
2. **Editor merge pass.** Fold duplicates, merge weak siblings into stronger
   parents (23 → 14).
3. **Adversarial judge panel.** Score every concept on weighted criteria. The
   original weights: **brand fit 45% · distinctiveness 30% · feasibility 25%**.
   ⬜ Confirm the weights for Meristem.
4. **Verify blockers against the repo, not assumptions.** Check every concept's
   factual premises (does that page exist? does the library expose that API? is
   that number real?). Several top-sounding concepts died here.
5. **Categorize the survivors:**
   - *Front-runners* — build candidates, ranked.
   - *Systems* — site-wide vocabularies (hover/press/reveal grammar, dividers,
     failure states), with usage rules or they decay into decoration.
   - *Set pieces* — one-off hero moments, each with an owner page.
   - *Governance* — the budget and its named exemptions.
   - *Cut, with reasons* — keep the reasoning; it prevents re-litigating.
6. **Prototype in labs, not pages.** Standalone lab pages (`motion-lab.html` here;
   the original grew `header-lab` and `scroll-lab`) where variants sit side by side.
   Iterate in versions; keep a **dated ledger** of every change and its rationale in
   this doc, marking superseded entries instead of deleting them.
7. **Stakeholder sync on the lab**, not on production pages. Quick fixes and
   replacement concepts get their own ledger entries.
8. **Integrate winners to pages** — and when pages duplicate CSS, **carry every fix
   to every page that duplicates it** (a real bug class; see gotchas).

## What to work out for the Meristem site

- ⬜ The doctrine sentence: what every set piece resolves to.
- ⬜ An **ownable visual notation** to animate. The original's edge was animating
  its own diagram grammar (branded node/edge/breakpoint notation) instead of stock
  effects — the brainstorm converged *away* from GPU shaders and toward SVG notation
  motion as both cheaper and more distinctive. Meristem needs its equivalent before
  set pieces are worth building. (The shader island remains available as a backdrop,
  but treat it as texture, not as the signature.)
- ⬜ Which pages get a set piece, and which are deliberately still.
- ⬜ The systems vocabulary: hover/underline rules, section dividers, form/failure
  states, cross-page transitions.
- ⬜ Scoring weights and the judge-panel pass over Meristem-specific concepts.

## Primitives (`motion.css`)

De-branded, production-hardened building blocks. All are driven by per-element
custom properties (`--delay`, `--dur`, …), run once (`forwards`/`both`), and carry
`prefers-reduced-motion` fallbacks that land on the final frame. See
`motion-lab.html` for live examples.

| Class | What it does | Knobs |
|---|---|---|
| `.mo-draw` | SVG path draws itself in (requires `pathLength="1"` on the path) | `--dur`, `--delay` |
| `.mo-pop` | SVG node scales in with a slight overshoot | `--delay` |
| `.mo-fade` | Simple fade-in at its cue | `--delay` |
| `.mo-settle` | Element glides from a scattered offset into its resting place | `--tx`, `--ty`, `--rot`, `--dur`, `--delay` |
| `.mo-flow` | A dash of "work" travels along a path (requires `pathLength="200"`) | `--dash`, `--dur`, `--delay`, `--ease` |
| `.mo-out` | Staged fade-out for scaffolding that should leave the scene | `--exit` |
| `.mo-sweep` | Highlight ink sweeps under text, once, and stays | `--sweep-dur`, `--sweep-delay`, `--sweep-color` |
| `.flip-tile` | Hover/focus flips a card to its back face | markup pattern in lab |
| `.logo-marquee` | Edge-masked logo strip, pauses on hover, wraps statically under reduced motion | markup pattern in lab |

Plus `reveal.js` (already in the repo): the enter-once **scroll register**. Tag a
whole section container with `data-enter`; it rises once on first entry and latches.

## Gotchas (paid for in production — don't rediscover them)

- **A round `stroke-linecap` paints a dot even on a fully retracted dash.** Never
  rely on `stroke-dashoffset` alone to hide an undrawn path — keep it at `opacity:0`
  until its cue (`.mo-draw` does this).
- **A `scale(0)` circle still paints a speck** in some renderers. Opacity does the
  hiding; transform only does the motion (`.mo-pop` does this).
- **The unit of scroll reveal is a whole section block, never an individual heading
  or card** — a heading animating over static body text below it reads broken.
  One block, one movement; no stagger.
- **The first content section under a hero stays untagged** — the hero just
  performed; the section below it should already be at rest when the reader arrives.
- **Choreography timing is a dependency graph.** Cue comments like "highlight
  completes as the route finishes inking (~4.4s)" belong next to the values;
  when you retime one element, walk the whole timeline.
- **Pages that duplicate set-piece CSS must all receive every fix.** Prefer keeping
  primitives in `motion.css` and only the scene-specific timeline inline on the page.

---

## Ledger

Dated entries for every lab iteration, review outcome, and integration pass go here,
newest last. Mark superseded entries instead of deleting them.

- **2026-07-31** — Program extracted from the original production repo; primitives
  de-branded into `motion.css`; lab seeded with one example per primitive.
