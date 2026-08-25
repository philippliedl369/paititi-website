// Retreat Guru links back to "our website" from its own pages — the centre's
// programs list, and each teacher profile such as
// https://paititi-institute.secure.retreat.guru/teacher/roman-hanis/. It builds
// those links from one field in the Retreat Guru admin, as
//
//     <website>/?programs=1&program=<id>
//
// which is how the RBG Connect widget deep-links into a program when the widget
// is embedded on the page that field names. Through the migration that field
// still read paititi-institute.squarespace.com, so every one of those links led
// back to the old Squarespace site (Roman, 25 Aug 2026).
//
// Our widget lives inside an iframe (/rbg-widget.html), so the query string
// never reaches it and the deep link would otherwise just sit unused on
// whichever page it landed on. This maps the program id onto the page that
// actually presents that program, so the field can simply be set to
// https://paititi-institute.org and every link resolves.
//
// Ids come from the links Retreat Guru itself emits; re-read them from the
// teacher page above if a program is added or replaced. An unrecognised id is
// left alone on purpose — better a real page with a stray query string than a
// confident redirect to the wrong program.
(() => {
  var DESTINATIONS = {
    614: '/online-courses#your-evolutionary-blueprint',    // Your Evolutionary Blueprint
    632: '/online-courses#alchemy-of-immortality-qigong',  // Alchemy of Immortality Daoist QiGong / Andean Art of Being
    638: '/online-courses#primordial-breathwork',          // Primordial Breathwork
    997: '/online-courses#practical-alchemy-series',       // Beyond Ayahuasca book Practical Alchemy Series
    1046: '/retreats',                                     // Amazon: 16-day Embodying True Nature Immersion
  };

  var id = new URLSearchParams(location.search).get('program');
  if (!id || !/^\d+$/.test(id)) return;
  var to = DESTINATIONS[id];
  if (!to) return;
  // replace(), not assign(): the query-string URL is a redirect step, not a
  // page the reader should be able to go Back to.
  if (location.pathname + location.hash !== to) location.replace(to);
})();
