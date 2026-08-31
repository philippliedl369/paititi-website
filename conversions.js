/* Google Ads conversion tracking.
 *
 * Google Ads knows how many people clicked an ad. It cannot see what they did
 * next, because that happens here. A conversion action is the signal back:
 * *this visitor did the thing we wanted.* Without one the console can only
 * report "412 clicks"; with one it reports which of those clicks led to a
 * booking. The Ad Grant also requires it — a grant account that records no
 * conversions for long enough is suspended, and Google does not accept a bare
 * page view as the only conversion, which is what the action their signup flow
 * offered to create was.
 *
 * What is countable and what is not:
 *
 *   Donations complete inside the embedded Zeffy form and bookings inside
 *   Retreat Guru. Both are other people's domains, so the completed
 *   transaction is invisible to this site — nothing here can see it, and no
 *   amount of code will change that. What is counted is the *click through* to
 *   them. That is what nearly every nonprofit site counts, but it means a
 *   report reading "9 conversions" means nine people went to the donation
 *   form, not nine donations. Don't read it as revenue.
 *
 * No value or currency is sent. The snippet Google hands you hardcodes
 * `value: 1.0, currency: 'USD'`, which overrides whatever the conversion
 * action is configured with and makes every action worth the same. A booking
 * click is not worth a newsletter signup; set the value per action in the Ads
 * UI, where it can be changed without a deploy, and leave it out here.
 *
 * Why a delegated listener rather than the onclick Google's snippet expects:
 *
 *   Their snippet is written to be called from `onclick="return
 *   gtag_report_conversion(url)"`. The DC runtime strips event-handler
 *   attributes, so that handler would simply not exist in the rendered page —
 *   no error, no warning, a conversion that never fires. And the page is
 *   re-rendered out of <x-dc> after load, which detaches anything bound
 *   directly to an element. One listener on `document` survives both.
 *   consent.js is the other worked example.
 *
 *   Their `event_callback` / `window.location` dance is not needed either: it
 *   exists to delay a same-tab navigation until the beacon is away, and every
 *   CTA this file matches is already target="_blank".
 *
 * Consent: the tag denies ad_storage until a visitor accepts (see
 * tools/apply_analytics.py). Conversions are still sent while denied — without
 * cookies, and modelled by Google rather than attributed to a person. That is
 * the intended behaviour of Consent Mode, not a bug to route around.
 */
(function () {
  'use strict';

  /* One conversion label per action, from Google Ads → Goals → Conversions.
   *
   * `null` means the action has not been created in Ads yet: nothing is sent,
   * nothing breaks, and it starts working the moment a label is pasted in.
   * Making up a label would not fail loudly — it would silently record
   * nothing — so an empty slot is left empty on purpose.
   *
   * `booking` carries the one label that exists so far. It is the action the
   * Ads signup flow created under the name "Page view"; it is Click-based and
   * now fires on register clicks, so it needs renaming in the Ads UI to match
   * what it actually counts.
   */
  var ACTIONS = {
    booking: 'AW-18415578586/oQgjCKybuOscENrbnc1E',
    donate: null,
    contact: null,
    subscribe: null,
  };

  function fire(name) {
    var sendTo = ACTIONS[name];
    if (!sendTo) return;
    if (typeof window.gtag !== 'function') return;   // tag blocked, or offline
    window.gtag('event', 'conversion', { send_to: sendTo });
  }

  /* Which outbound links are worth counting.
   *
   * Matched on the parsed hostname rather than a substring of the href, so
   * `retreat.guru.example.com` cannot pass. The /program/ test matters: the
   * same host also serves the photographs used on the initiative pages, out of
   * /wp-content/, and a click on a photo is not a booking.
   */
  function actionFor(a) {
    var host = (a.hostname || '').toLowerCase();
    if (/(^|\.)retreat\.guru$/.test(host) && a.pathname.indexOf('/program/') === 0) return 'booking';
    if (/(^|\.)zeffy\.com$/.test(host)) return 'donate';
    return null;
  }

  document.addEventListener('click', function (e) {
    // Something else already cancelled this click, so no navigation follows
    // and there is nothing to count.
    if (e.defaultPrevented) return;
    var a = e.target && e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var name = actionFor(a);
    if (name) fire(name);
  });

  /* The two forms post through fetch and never navigate, so there is no click
   * to catch: they call this from their own success branch instead, once the
   * server has actually accepted the submission. A form that was filled in and
   * then failed is not a conversion.
   *
   * The contact form carries a newsletter opt-in that rides along with the
   * message. It deliberately does not also count as `subscribe` — one form
   * submitted is one conversion, or a single visitor doing a single thing
   * would show up twice in the reports.
   */
  window.ptConversion = fire;
})();
