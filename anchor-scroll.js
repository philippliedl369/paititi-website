// Pages render client-side (support.js): on a direct visit to /page#section the
// browser's native fragment jump targets the raw <x-dc> template, which boot()
// then replaces with the React-rendered #dc-root — resetting scroll to 0. So
// the native jump always gets undone. Wait for the target to exist inside the
// rendered #dc-root, jump there, and re-assert once the render burst settles.
// Instant (not smooth) on purpose: that matches native load-time anchor
// behavior; smooth scrolling stays for in-page clicks.
(() => {
  let userScrolled = false;
  const markScrolled = () => { userScrolled = true; };
  addEventListener('wheel', markScrolled, { passive: true, once: true });
  addEventListener('touchmove', markScrolled, { passive: true, once: true });

  function target() {
    const id = location.hash.slice(1);
    if (!id) return null;
    const root = document.getElementById('dc-root');
    if (!root) return null;
    let el = null;
    try {
      el = document.getElementById(decodeURIComponent(id));
    } catch {
      el = document.getElementById(id);
    }
    return el && root.contains(el) ? el : null;
  }

  function jump() {
    const el = target();
    if (el && !userScrolled) el.scrollIntoView({ behavior: 'instant', block: 'start' });
    return !!el;
  }

  function start() {
    if (!location.hash) return;
    let found = false;
    let settleTimer = 0;
    const mo = new MutationObserver(() => {
      if (!found && jump()) found = true;
      if (!found) return;
      // Later mutations (second-pass template fetch, streaming imports) can
      // shift layout; re-assert once the DOM goes quiet, then stop watching.
      clearTimeout(settleTimer);
      settleTimer = setTimeout(() => {
        jump();
        mo.disconnect();
      }, 400);
    });
    mo.observe(document.documentElement, { childList: true, subtree: true });
    jump();
    setTimeout(() => mo.disconnect(), 10000);
  }

  if (document.readyState === 'loading') {
    addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
