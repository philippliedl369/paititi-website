/* Ambient video behind a hero photo.
 *
 * A section carrying data-video="/assets/video/x.mp4" and a .pt-sec-bg keeps
 * its <img> as the design: that still is the LCP image, the no-JS page, the
 * reduced-motion page and the phone page. When the viewport is a desktop, the
 * visitor has not asked for reduced motion or data saving, and the file
 * actually plays, a muted looping <video> is layered over the still and faded
 * in — frame 0 of the clip is the still, so nothing visibly changes except
 * that the sky starts to move. Any failure (404, codec, autoplay blocked)
 * removes the video and leaves the photo.
 *
 * Timing: support.js hides the raw <x-dc> markup (display:none) and renders
 * the page from it after DOMContentLoaded, so the same <section> exists twice
 * over the page's life — first as hidden source, then as the laid-out copy.
 * Mounting into the hidden source is wasted (the runtime discards it), which
 * is why a section only counts once it has a layout box, and why the observer
 * keeps watching until a mounted video is still attached after the render
 * settles. See tools/hero-video/README.md.
 */
(function () {
  'use strict';

  var WANT = '(min-width: 1181px) and (prefers-reduced-motion: no-preference)';
  var SETTLE_MS = 8000;   // keep watching for re-renders this long after a mount

  function allowed() {
    if (!window.matchMedia || !window.matchMedia(WANT).matches) return false;
    var c = navigator.connection;
    if (c && c.saveData) return false;
    return true;
  }

  function mount(section) {
    var bg = section.querySelector('.pt-sec-bg');
    var src = section.getAttribute('data-video');
    if (!bg || !src) return null;

    var v = document.createElement('video');
    v.muted = true;            // the property, not only the attribute: autoplay policy checks the property
    v.defaultMuted = true;
    v.loop = true;
    v.autoplay = true;
    v.playsInline = true;
    v.setAttribute('muted', '');
    v.setAttribute('playsinline', '');
    v.setAttribute('aria-hidden', 'true');
    v.setAttribute('tabindex', '-1');
    v.preload = 'auto';
    v.disablePictureInPicture = true;
    v.className = 'pt-hero-video';

    var dead = false;
    function remove() {
      if (dead) return;
      dead = true;
      section.setAttribute('data-video-failed', '');   // don't try this section again
      if (v.parentNode) v.parentNode.removeChild(v);
    }

    // A 404 or an undecodable file fires `error`; a slow network only fires
    // `stalled`/`waiting`, which is not a reason to give up — the photo is
    // showing underneath the whole time. Only reveal once real frames are
    // flowing, so a slow decode never shows a black rectangle over it.
    v.addEventListener('error', remove);
    v.addEventListener('playing', function () { v.classList.add('is-on'); }, { once: true });

    v.src = src;
    bg.appendChild(v);

    var p = v.play();
    if (p && typeof p.catch === 'function') p.catch(remove);

    // Don't burn a decoder while the hero is scrolled off-screen.
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (dead) return;
          if (e.isIntersecting) { var r = v.play(); if (r && r.catch) r.catch(function () {}); }
          else v.pause();
        });
      }, { threshold: 0 }).observe(section);
    }
    return v;
  }

  if (!allowed()) return;

  var video = null;         // the mounted element, if any
  var mountedAt = 0;
  var pending = false;

  function scan() {
    if (video && video.isConnected) return;          // still attached, nothing to do
    if (video && !video.isConnected) video.pause();  // the render replaced our section
    video = null;
    var sections = document.querySelectorAll('section[data-video]:not([data-video-failed])');
    for (var i = 0; i < sections.length; i++) {
      var s = sections[i];
      if (s.getClientRects().length === 0) continue; // hidden source markup, not the rendered page
      if (s.querySelector('video.pt-hero-video')) { video = s.querySelector('video.pt-hero-video'); return; }
      video = mount(s);
      if (video) { mountedAt = Date.now(); return; }
    }
  }

  function schedule() {
    if (pending) return;
    pending = true;
    requestAnimationFrame(function () { pending = false; scan(); });
  }

  var mo = null;
  if ('MutationObserver' in window) {
    mo = new MutationObserver(schedule);
    mo.observe(document.documentElement, { childList: true, subtree: true });
  }
  // Poll as well, so a render that lands between frames or before the observer
  // is still caught; stop once a mount has survived SETTLE_MS of quiet, or
  // after GIVE_UP_MS in any case (nothing to mount, or the file is missing).
  var GIVE_UP_MS = 30000;
  var startedAt = Date.now();
  var t = setInterval(function () {
    scan();
    var settled = video && video.isConnected && Date.now() - mountedAt > SETTLE_MS;
    if (settled || Date.now() - startedAt > GIVE_UP_MS) {
      clearInterval(t);
      if (mo) mo.disconnect();
    }
  }, 250);
})();
