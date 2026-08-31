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
 * Two things worth knowing before editing:
 *
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
      text: 'We use cookies to understand how this site is used. Declining keeps everything working — we simply will not measure the visit.',
      accept: 'Accept',
      decline: 'Decline',
      privacy: 'Privacy Policy',
      privacyHref: '/who/privacy-policy',
      label: 'Cookie consent',
    },
    es: {
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

  var STYLE = [
    '.pt-consent{position:fixed;left:0;right:0;bottom:0;z-index:' + Z + ';',
    '  background:#2A1736;color:#fff;box-shadow:0 -2px 24px rgba(33,4,22,.34)}',
    /* The banner is a strip, not a modal: it never covers the page's own
       controls, and the measured layout above it does not move. */
    '.pt-consent-in{max-width:1200px;margin:0 auto;padding:20px 24px;display:flex;',
    '  gap:20px;align-items:center;flex-wrap:wrap}',
    '.pt-consent p{margin:0;flex:1 1 380px;font-size:15.5px;line-height:1.7;color:#fff}',
    '.pt-consent a{color:#F1EAF6;text-decoration:underline;text-underline-offset:3px}',
    '.pt-consent-btns{display:flex;gap:12px;flex:0 0 auto}',
    '.pt-consent button{font:inherit;font-size:15.5px;cursor:pointer;border-radius:2px;',
    '  padding:11px 26px;border:1px solid #F1EAF6;background:transparent;color:#F1EAF6;',
    '  transition:background .18s ease,color .18s ease}',
    '.pt-consent button.is-primary{background:#F1EAF6;color:#210416}',
    '.pt-consent button:hover{background:#fff;color:#210416}',
    '.pt-consent button:focus-visible{outline:2px solid #fff;outline-offset:3px}',
    /* Phones: the two buttons go full width and side by side, so neither is a
       small target and the strip stays two short rows. */
    '@media (max-width:640px){',
    '  .pt-consent-in{padding:16px;gap:14px}',
    '  .pt-consent p{flex:1 1 100%;font-size:14.5px}',
    '  .pt-consent-btns{flex:1 1 100%}',
    '  .pt-consent button{flex:1 1 50%;padding:12px 10px}}',
    '@media (prefers-reduced-motion:no-preference){',
    '  .pt-consent{animation:pt-consent-in .32s ease-out both}',
    '  @keyframes pt-consent-in{from{transform:translateY(100%)}to{transform:none}}}',
  ].join('');

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

    var wrap = document.createElement('div');
    wrap.className = 'pt-consent-in';

    var p = document.createElement('p');
    p.appendChild(document.createTextNode(t.text + ' '));
    var a = document.createElement('a');
    a.href = t.privacyHref;
    a.textContent = t.privacy;
    p.appendChild(a);

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
    wrap.appendChild(p);
    wrap.appendChild(btns);
    el.appendChild(wrap);
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
