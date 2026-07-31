// Enter-once scroll reveals — the "ink that stays" scroll register
// (docs/animation-concepts.md, "Scroll register", 2026-07-30).
//
// The unit of reveal is a whole SECTION BLOCK, never an individual heading or
// card: a section's container div carries [data-enter] and its heading and body
// rise together. (Revised 2026-07-30 after review — the first pass tagged
// headings and cards separately, which let a heading animate over static body
// text below it. Heading and body must arrive as one.) Consequently there is no
// stagger and no per-element delay: one block, one movement.
//
// Tagged blocks rise into their resting position the first time they enter the
// viewport, then latch: the observer unobserves them and nothing ever re-runs —
// ink is never retracted. Section headings carrying .ink-rule draw their amber
// rule as the block lands.
//
// The first content section of each page is deliberately NOT tagged: it sits
// directly under a hero that just performed its set piece, and that section
// should already be at rest when the reader arrives. Heroes, CTA bands, logo
// marquees, Contact, the blog and AI4 are untagged for the same
// register reasons.
//
// Pages render client-side (support.js boot() → #dc-root) and later template
// passes can replace nodes, so tagged elements are discovered with a
// MutationObserver as they appear — same reason anchor-scroll.js watches the
// DOM instead of reading it once.
//
// The hiding CSS is injected from here on purpose: with no JS, or with
// prefers-reduced-motion, the style never exists and the page rests in its
// final designed state — including the full-width amber rules, which are part
// of the design (each page carries its own static .ink-rule CSS), not a
// motion artifact.
(() => {
  if (!('IntersectionObserver' in window)) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ease = 'cubic-bezier(.4,0,.2,1)';
  const style = document.createElement('style');
  style.textContent =
    `[data-enter]{opacity:0;transform:translateY(24px);` +
    `transition:opacity .34s ${ease},transform .52s ${ease}}` +
    `[data-enter="in"]{opacity:1;transform:translateY(0)}` +
    `[data-enter] .ink-rule::after{width:0;transition:width .5s ${ease} .18s}` +
    `[data-enter="in"] .ink-rule::after{width:var(--rule-w,64px)}` +
    `@media print{[data-enter]{opacity:1;transform:none}}`;
  document.head.appendChild(style);

  const io = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.setAttribute('data-enter', 'in');
      io.unobserve(entry.target); // the latch: runs once, ends at rest
    }
  }, { threshold: 0.2, rootMargin: '0px 0px -8% 0px' });

  const seen = new WeakSet();
  function scan() {
    document.querySelectorAll('[data-enter]').forEach((el) => {
      if (seen.has(el) || el.getAttribute('data-enter') === 'in') return;
      seen.add(el);
      io.observe(el);
    });
  }

  function start() {
    scan();
    new MutationObserver(scan).observe(document.documentElement, { childList: true, subtree: true });
  }
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', start);
  else start();
})();
