/* Cookie consent, wired to Google Consent Mode v2.
 *
 * The Google tag in every page's <head> now declares its consent *defaults*
 * before gtag.js loads: everything that stores or shares data is denied until
 * a visitor says otherwise. That inline block also restores a previous answer
 * synchronously, so someone who already accepted is measured from their very
 * first page rather than from the second — see tools/apply_analytics.py.
 *
 * This file is only the conversation: it draws the banner, records the answer
 * and sends the `update`. Nothing here is required for the page to work, which
 * is why it is deferred and why a failure to load leaves analytics denied
 * rather than granted.
 *
 * Three things worth knowing before editing:
 *
 *   - It is styled as chrome, not as page content. The banner is appended to
 *     <body>, outside `.pt-page`, so it inherits no type at all — font family
 *     and tracking have to be declared here, exactly as SiteHeader and
 *     SiteFooter declare their own. Left out, it renders in the browser's
 *     default serif, which is what it did until 1 Sep.
 *   - Declining is a real answer, not a dismissal. There is no close button
 *     that leaves the question open, because "denied" has to be a choice the
 *     visitor can make in one click, and a banner that can only be accepted is
 *     not consent.
 *   - The answer is withdrawable. window.ptConsent.open() reopens the banner,
 *     and the footer link calls it. Consent you cannot take back is not
 *     consent either.
 *
 * Language comes from <html lang>, like the rest of the bilingual tree. No
 * runtime translation layer, just the two strings.
 */
(function () {
  'use strict';

  var KEY = 'pt-consent';          // 'granted' | 'denied'
  var Z = 9990;

  var COPY = {
    en: {
      title: 'A note on cookies',
      text: 'We use cookies to understand how this site is used. Declining keeps everything working — we simply will not measure the visit.',
      accept: 'Accept',
      decline: 'Decline',
      privacy: 'Privacy Policy',
      privacyHref: '/who/privacy-policy',
      label: 'Cookie consent',
    },
    es: {
      title: 'Sobre las cookies',
      text: 'Usamos cookies para entender cómo se usa este sitio. Si prefieres rechazarlas, todo sigue funcionando igual: simplemente no mediremos la visita.',
      accept: 'Aceptar',
      decline: 'Rechazar',
      privacy: 'Política de privacidad',
      privacyHref: '/es/politica-de-privacidad',
      label: 'Consentimiento de cookies',
    },
  };

  var lang = (document.documentElement.getAttribute('lang') || 'en').slice(0, 2).toLowerCase();
  var t = COPY[lang] || COPY.en;

  function stored() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function remember(value) {
    try { localStorage.setItem(KEY, value); } catch (e) { /* private mode: the answer lasts this visit only */ }
  }

  // The same signal set the <head> block denies by default. Sent again on every
  // answer so a change of mind reaches Google immediately, not on next load.
  function send(granted) {
    var state = granted ? 'granted' : 'denied';
    if (typeof window.gtag !== 'function') return;
    window.gtag('consent', 'update', {
      ad_storage: state,
      ad_user_data: state,
      ad_personalization: state,
      analytics_storage: state,
    });
  }

  /* The banner is the footer's newsletter panel in miniature, which is where
     the site's dark-ground vocabulary already lives: deep plum, the 40px/0
     asymmetric corner, a Philosopher line over Lato Light copy, and the
     16px/0 corner on the buttons.

     Two things here are not decoration:

       - `font-family` on `.pt-consent`. The banner is appended to <body>,
         *outside* `.pt-page`, so it inherits none of the page's type — before
         this it rendered in the browser's default serif on every page. The
         same applies to `letter-spacing`: the .08em site tracking is declared
         on `.pt-page main` (and again on the header and footer, which are also
         outside it), so chrome components have to declare their own. .08em
         against this font size is the footer's rule, not a new value.
       - It is a card in the corner, not a modal and not a full-bleed strip.
         Nothing on the page moves, nothing is behind an overlay, and the
         window it covers is a corner rather than the whole bottom band. */
  var STYLE = [
    '.pt-consent{position:fixed;left:24px;bottom:24px;z-index:' + Z + ';',
    '  width:min(430px,calc(100vw - 48px));',
    '  font-family:var(--font-body,"Lato",system-ui,-apple-system,"Segoe UI",sans-serif);',
    /* 17.6px only so `.08em` resolves to the site's 1.408px and is inherited as
       px by everything below, exactly as .pt-footer does it. Nothing in the card
       actually renders at 17.6px except the buttons, which set it themselves. */
    '  font-size:17.6px;font-weight:300;letter-spacing:.08em;color:#fff;',
    '  background:linear-gradient(158deg,#331C41 0%,#2A1736 56%,#210416 100%);',
    '  border-radius:40px 0;padding:30px 32px 32px;',
    /* Hairline as an inset shadow rather than a border, so it cannot add to the
       box and shift the padding — the same trick the hero ghost button uses. */
    '  box-shadow:inset 0 0 0 1px rgba(241,234,246,.16),0 18px 48px rgba(20,3,14,.44)}',
    /* `.pt-consent` itself, not only its children: the width above is a
       border-box figure, and without this the 32px padding is added to it. */
    '.pt-consent,.pt-consent *,.pt-consent *::before,.pt-consent *::after{box-sizing:border-box}',

    /* Badge and title share a row: at this measure a stacked mark would cost a
       line of height and read as an illustration rather than a label. */
    '.pt-consent-head{display:flex;align-items:center;gap:14px;margin:0 0 14px}',
    '.pt-consent-mark{flex:0 0 auto;display:inline-flex;align-items:center;justify-content:center;',
    '  width:40px;height:40px;border-radius:50%;background:rgba(241,234,246,.13);color:#C9A7E0}',
    '.pt-consent h2{margin:0;font-family:var(--font-display,"Philosopher",Georgia,serif);',
    '  font-weight:400;font-size:24px;line-height:1.3;letter-spacing:normal;color:#fff}',

    '.pt-consent p{margin:0 0 16px;font-size:15.5px;font-weight:300;line-height:1.72;',
    '  color:rgba(255,255,255,.86)}',
    /* The privacy link gets its own line at the site's small size. Inline at the
       end of the copy it broke across two lines mid-link, which reads as a typo. */
    '.pt-consent-more{display:block;margin:0 0 22px;font-size:14.272px;font-weight:300}',
    '.pt-consent a{color:#F1EAF6;text-decoration:underline;text-underline-offset:4px;',
    '  transition:color .18s ease}',
    '.pt-consent a:hover{color:#fff}',

    '.pt-consent-btns{display:flex;gap:12px}',
    /* Both buttons carry the site's button shape and Lato Bold at the body
       size; only the fill separates them, so neither is visually the default. */
    '.pt-consent button{flex:1 1 50%;min-height:50px;padding:0 22px;cursor:pointer;',
    '  display:inline-flex;align-items:center;justify-content:center;',
    '  font-family:inherit;font-size:17.6px;font-weight:700;letter-spacing:.02em;',
    '  border:0;border-radius:16px 0;background:transparent;color:#F1EAF6;',
    '  box-shadow:inset 0 0 0 1.5px rgba(241,234,246,.42);',
    '  transition:background .2s ease,color .2s ease,box-shadow .2s ease}',
    '.pt-consent button:hover{background:rgba(241,234,246,.14);color:#fff;',
    '  box-shadow:inset 0 0 0 1.5px rgba(241,234,246,.7)}',
    '.pt-consent button.is-primary{background:#F1EAF6;color:#2A1736;box-shadow:none}',
    '.pt-consent button.is-primary:hover{background:#fff;color:#210416;box-shadow:none}',
    '.pt-consent button:focus-visible{outline:2px solid #fff;outline-offset:3px}',

    /* Phones: a corner card at 390px is a card with no corner left, so it
       becomes a sheet with side margins — full-measure buttons, the smaller
       32px/0 corner the footer panel uses at this width, and clearance for
       the iOS home bar. */
    '@media (max-width:640px){',
    '  .pt-consent{left:12px;right:12px;width:auto;border-radius:32px 0;',
    '    bottom:calc(12px + env(safe-area-inset-bottom,0px));padding:24px 22px 26px}',
    '  .pt-consent-head{gap:12px;margin-bottom:12px}',
    '  .pt-consent-mark{width:36px;height:36px}',
    '  .pt-consent h2{font-size:21px}',
    '  .pt-consent p{font-size:15px;margin-bottom:14px}',
    '  .pt-consent-more{margin-bottom:18px}',
    '  .pt-consent button{padding:0 10px}}',
    /* The buttons are already over the 44px minimum; this pins them against a
       future size change, the way the footer's button does. The privacy link is
       the one control here that is genuinely too small — a 14.272px line box is
       about 17px — so it gets padding, with the margin pulled back by the same
       amount so nothing about the card's spacing changes. Same technique as
       .pt-foot-links. */
    '@media (pointer:coarse){',
    '  .pt-consent button{min-height:50px}',
    '  .pt-consent-more{padding:8px 0;margin-top:-8px;margin-bottom:14px}}',
    '@media (prefers-reduced-motion:no-preference){',
    '  .pt-consent{animation:pt-consent-rise .42s cubic-bezier(.2,0,0,1) both}',
    '  @keyframes pt-consent-rise{',
    '    from{opacity:0;transform:translateY(18px) scale(.97)}',
    '    to{opacity:1;transform:none}}}',
  ].join('');

  // A sprouting leaf, in the same 24-grid, 1.6px round-capped stroke as the
  // header and footer icons. createElementNS matters: an <svg> built with
  // createElement lands in the HTML namespace and renders as nothing.
  function leaf() {
    var NS = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', '21');
    svg.setAttribute('height', '21');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '1.6');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');
    // Lucide's `leaf`, transcribed the way SiteHeader transcribes its social
    // marks. Drawn by hand at first and it read as a blob at 21px — this one is
    // designed for exactly this size.
    ['M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z',
     'M2 21c0-3 1.85-5.36 2.99-7.01A12.5 12.5 0 0 1 8 6'].forEach(function (d) {
      var path = document.createElementNS(NS, 'path');
      path.setAttribute('d', d);
      svg.appendChild(path);
    });
    return svg;
  }

  var el = null;

  function close() {
    if (el && el.parentNode) el.parentNode.removeChild(el);
    el = null;
  }

  function answer(granted) {
    remember(granted ? 'granted' : 'denied');
    send(granted);
    close();
  }

  function open() {
    if (el) return;
    if (!document.getElementById('pt-consent-style')) {
      var s = document.createElement('style');
      s.id = 'pt-consent-style';
      s.textContent = STYLE;
      document.head.appendChild(s);
    }

    el = document.createElement('aside');
    el.className = 'pt-consent';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-live', 'polite');
    el.setAttribute('aria-label', t.label);

    // The leaf is built as real SVG elements rather than a CSS background: a
    // data-URI SVG in a stylesheet gets its viewBox mangled (see CLAUDE.md),
    // and this way it inherits currentColor like the header's social marks.
    var head = document.createElement('div');
    head.className = 'pt-consent-head';
    var mark = document.createElement('span');
    mark.className = 'pt-consent-mark';
    mark.setAttribute('aria-hidden', 'true');
    mark.appendChild(leaf());
    var h = document.createElement('h2');
    h.textContent = t.title;
    head.appendChild(mark);
    head.appendChild(h);

    var p = document.createElement('p');
    p.textContent = t.text;

    var a = document.createElement('a');
    a.className = 'pt-consent-more';
    a.href = t.privacyHref;
    a.textContent = t.privacy;

    var btns = document.createElement('div');
    btns.className = 'pt-consent-btns';

    var decline = document.createElement('button');
    decline.type = 'button';
    decline.textContent = t.decline;
    decline.addEventListener('click', function () { answer(false); });

    var accept = document.createElement('button');
    accept.type = 'button';
    accept.className = 'is-primary';
    accept.textContent = t.accept;
    accept.addEventListener('click', function () { answer(true); });

    btns.appendChild(decline);
    btns.appendChild(accept);
    el.appendChild(head);
    el.appendChild(p);
    el.appendChild(a);
    el.appendChild(btns);
    document.body.appendChild(el);
    // Focus the strip, not a button. Moving focus in is what a screen reader
    // and a keyboard need; landing it on "Accept" would put a focus ring on one
    // of two equal choices and quietly recommend it.
    el.setAttribute('tabindex', '-1');
    el.focus({ preventScroll: true });
  }

  // Reopening is how consent is withdrawn.
  window.ptConsent = {
    open: function () { open(); },
    state: function () { return stored() || 'unset'; },
  };

  // The footer's "Cookie Settings" link is a plain href="#cookie-settings", and
  // this listens for it on the document rather than binding to the element.
  // Two reasons, both learned the hard way: the DC runtime strips inline
  // onclick attributes (they simply do not survive the render), and the footer
  // is re-rendered out of <x-dc> after load, which would detach any listener
  // bound directly to the link. Delegation survives both. Capture phase, so it
  // runs before anchor-scroll.js goes looking for an element with that id.
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest && e.target.closest('a[href="#cookie-settings"]');
    if (!a) return;
    e.preventDefault();
    e.stopPropagation();
    open();
  }, true);

  function start() {
    if (!stored()) open();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }

  // support.js renders the page out of <x-dc> after DOMContentLoaded. That
  // appends to <body> rather than replacing it, so the banner survives — but it
  // costs nothing to make sure, and a detached banner would be a silent failure
  // of the one thing on the page that has to work.
  var checks = 0;
  var t2 = setInterval(function () {
    if (++checks > 20) return clearInterval(t2);
    if (el && !el.isConnected) document.body.appendChild(el);
  }, 250);
})();
