# Moving paititi-institute.org to Cloudflare

Updated 24 Aug 2026. The Cloudflare account exists, Stripe is not used, and
the store is gone. The newsletter has to leave Squarespace eventually — it has
no subscribe API, so a new site could only ever feed it by hand — but that is
**not a launch task**: the site collects sign-ups itself from day one, and the
provider can be chosen at leisure. EmailOctopus is the standing recommendation
for the ~8,000-contact list; see the newsletter section for the costing.

**No deadline.** The Squarespace plans are paid into 2027, so the old site,
the domain and Email Campaigns all keep running while we cut over. Nothing
here has to be rushed and nothing has to be cancelled to go live — the only
irreversible step is the nameserver switch (Step 7), and even that reverses in
an hour. Exports are therefore housekeeping, not a race: do them whenever, just
do them **before anything is ever cancelled**, and keep auto-renew on until then.

---

## Part 1 — What we need

### Logins
1. **Cloudflare** — have it.
2. **Squarespace** — have it. It covers three things: the website, the domain
   (`paititi-institute.org` is registered there), and Email Campaigns.
3. **Resend** (resend.com, free) — for the contact form to reach info@. Create when ready.
4. **Google Search Console** — to resubmit the sitemap after the switch.

### Exports (where to click — no hurry, but do them before any cancellation)
- **Newsletter list** (~8,000 contacts — this is what moves to the new provider): Squarespace → your site → **Marketing → Email Campaigns → Mailing Lists** (newer accounts: **Contacts → Lists & Segments**) → hover the list → **⋯ → Export**. You get a .zip with three CSVs (subscribed / unsubscribed / cleaned). Keep all three.
- **Orders** (the old US Tour RSVP payments — records only, the store is not coming back): **Commerce → Orders** (newer UI: **Products & Services → Orders**) → **Export data → Download CSV**. Pick *All statuses* and the full date range.
- **Contacts** (customers + donors + subscribers in one): **Contacts** panel → **Export**.
- **Form submissions**, if any forms stored responses in Squarespace rather than emailing them: **Contacts**, or the form block's own storage — see **Settings → Form & Newsletter Storage**.
- **DNS screenshots**: Squarespace → **Domains → paititi-institute.org → DNS settings** — screenshot the entire page.

### The newsletter

**It has to move off Squarespace, and here is why.** Squarespace offers no way for
an outside website to add a subscriber: no API, and its hosted sign-up form is
not findable in this account. Staying on Squarespace therefore means exporting
and importing a CSV by hand forever, which is not a plan. Automations don't
rescue it either — "Tag Contacts who fill out a form" triggers on *"a form
completed on your site"*, meaning the Squarespace site, and Squarespace stops
automations once that site is offline.

So sign-ups go to a provider with an API. `api.js` speaks seven of them and all
seven are tested, so picking one is three values and no code:

```
NEWSLETTER_PROVIDER   emailoctopus | mailerlite | brevo | kit | mailchimp | beehiiv | resend
NEWSLETTER_API_KEY    that provider's key   (secret)
NEWSLETTER_LIST_ID    the list / group / form / audience id
```

**Nothing here is urgent.** The site collects sign-ups on its own from day one
(Step 6a). This is a decision to take calmly, not before launch.

#### What the 8,000-contact list costs

Free tiers are out — every one of them brands the emails. And at 8,000
contacts, *how* a provider charges matters more than its headline price. Some
bill per contact held, some per email sent. A list this size mailed once or
twice a month is the case where those two models diverge hardest:

| | ~8,000 contacts | Branding | Nonprofit |
|---|---|---|---|
| **EmailOctopus Pro** ⭐ | **~$24/mo**, unlimited sends | Removed on Pro | — |
| Brevo Starter | ~$18–32/mo by send volume, **+$9/mo** to remove branding | Surcharge | 15–20% |
| MailerLite Comfort | **~$90/mo** (your figure) → ~$63 with the 30% discount | Removed in plan | 30%, the highest |
| Kit / Mailchimp | Dearer again at this tier | Paid plans only | Mailchimp 15% |
| Resend | Marketing email bills by contact, from $40 at 5,000 | — | — |

**EmailOctopus is the recommendation: about $24/mo, roughly $290/year, against
$756/year for MailerLite even after its nonprofit discount.** It prices by
contact but sends without limit, which is exactly the right shape for a big
list mailed occasionally. Pro removes branding, and its API is already wired
up here.

The trade is that it is a smaller, plainer tool: solid campaigns, forms and
basic drip sequences, but nothing like MailerLite's automation builder. For a
newsletter — which is all this is — that costs nothing. **Send yourself a test
campaign before committing**, since deliverability is the one thing a price
comparison can't tell you.

Two reasons you might still pay MailerLite's premium, and they're legitimate:
the DNS **already** carries a MailerLite SPF include
(`include:_spf.mlsend.com`), so somebody once set sending up there — if that
account still exists with the list in it, the cheapest option is the one you
don't have to migrate to. And MailerLite runs a **Pay-it-forward** programme
giving selected nonprofits the Power plan free for two years, leaning toward
learning- and arts-based organisations. One email to ask; it would beat every
price in the table.

If you do go MailerLite, claim the **30% nonprofit discount** first: start the
14-day trial, pick *nonprofit* as the industry, and send support the fiscal
sponsor's IRS determination letter **within those 14 days**. It applies before
the first payment, and discounts don't stack.

#### Whoever wins

In the provider, not here: **verify the domain with SPF/DKIM/DMARC while we
still control DNS**, set the confirmation email (new sign-ups double opt in by
default), and put the postal address in the campaign footer — bulk email
legally needs it, and Squarespace used to supply it invisibly.

**Import the old list** from the Step 1 export. Import only the *subscribed*
file; the unsubscribed and cleaned files exist so you can honour those opt-outs,
not re-mail them. Re-mailing people who unsubscribed is how a domain's sending
reputation gets destroyed on day one.

### The store — removed 23 Aug 2026
Nothing was sold there but the US Tour RSVP donation, for an event that has
passed. Retreats and online courses book through Retreat Guru, and donations go
through Zeffy, so no cart is needed. The pages are deleted; `/store`,
`/store/*`, `/cart` and `/order-confirmed` now 301 to Programs and home so old
links and Google results don't hit a dead end. Recoverable from git if a shop is
ever wanted. No Stripe key is needed for anything on the new site.

### DNS records that must survive (re-read from the authoritative nameservers, 24 Aug 2026)
```
MX    @      1  aspmx.l.google.com.        ← Google Workspace email — critical
MX    @      5  alt1.aspmx.l.google.com.
MX    @      5  alt2.aspmx.l.google.com.
MX    @      10 alt3.aspmx.l.google.com.
MX    @      10 alt4.aspmx.l.google.com.
TXT   @      v=spf1 a mx include:_spf.mlsend.com ~all
TXT   @      google-site-verification=ivzXeym1DKcL_IvbRLC1VfM59qfEsHnv5lwseX-1kMs
TXT   @      google-site-verification=JQ0U4i7LILgU_tP2BCaFJRzhGQSWmVQvg-Kj9mtLLYo
TXT   @      google-site-verification=1o32nOtx_4Y5fJ18bf9sTxbY27yOpsMMSK-a21WBNZo
TXT   @      brevo-code:268dfc87244d85fd7b18362e4bf8f193
TXT   @      mailerlite-domain-verification=946625c1545d080d6432144ea8f498b5c06525b8
TXT   _dmarc v=DMARC1; p=none; rua=mailto:rua@dmarc.brevo.com
A     mail   50.87.248.165                 ← legacy mailbox host, DNS-only
CNAME imap   mail.paititi-institute.org.   ← DNS-only
CNAME pop    mail.paititi-institute.org.   ← DNS-only
```
Two traps in that list. The third `google-site-verification` record is stored with
a stray line-feed on the end — retype it clean, don't copy the mangled value. And
`mail` / `imap` / `pop` must be **DNS-only (grey cloud)** in Cloudflare; proxying
them breaks IMAP/SMTP, because the proxy only carries HTTP.

There is no CAA record, so nothing blocks Cloudflare from issuing a certificate.
`CNAME _domainconnect → _domainconnect.domains.squarespace.com` also exists; it is
only Squarespace's domain-setup helper and can be dropped or copied, either way.

Records pointing at Squarespace — `A @ 198.185.159.144/.145` and
`198.49.23.144/.145`, `CNAME www → ext-sq.squarespace.com` — are the ones we
replace, but copy them across anyway (DNS-only) so the nameserver switch changes
nothing visible; Step 8 replaces them. The Squarespace DNS screenshots remain the
source of truth for anything a scan misses.

### Secrets the site needs
One to launch: `RESEND_API_KEY` (contact form). Later, when a newsletter
provider is chosen: `NEWSLETTER_API_KEY` plus the plain variables
`NEWSLETTER_PROVIDER` and `NEWSLETTER_LIST_ID`. A missing contact key disables only the contact form,
which says "temporarily unavailable" and logs the real reason. A missing
newsletter key is softer: sign-ups fall back to our own storage, so nothing is
lost while the provider is being set up.

---

## Part 2 — Step by step

### Step 1 — Export everything (any time before a cancellation)
Follow the exports list above. Save to a shared Drive folder. The plans run
into 2027, so this is not blocking Step 3 onwards — it only has to happen
before Step 9.

### Step 2 — Screenshot DNS
Squarespace → Domains → paititi-institute.org → DNS settings. Scroll, screenshot all. Confirm auto-renew is on.

### Step 3 — Add the domain to Cloudflare (no nameserver change yet)
1. dash.cloudflare.com → **Add a domain** → `paititi-institute.org` → **Quick scan** → **Free** plan.
2. Compare the found records with the screenshots. Add anything missing (**Add record**, copy exactly).
3. Note the two nameservers Cloudflare shows (e.g. `ada.ns.cloudflare.com`). Click Continue; the check may fail for now — fine.

### Step 4 — Deploy to the test address
```bash
cd "paititi website"
npx wrangler login
npx wrangler deploy
```
Open the printed `…workers.dev` address and click through the site.

### Step 5 — Contact form key (Resend)
1. resend.com → **Domains → Add domain** → `paititi-institute.org` → it lists 2–3 DNS records → add them in Cloudflare → DNS.
2. **API Keys → Create** → copy the `re_…` key.
3. `npx wrangler secret put RESEND_API_KEY` (paste, Enter), or Cloudflare → Workers & Pages → paititi-institute → Settings → Variables and Secrets → Add secret.
4. Test the contact form on the workers.dev address after Step 7 (Resend needs the DNS live).

### Step 6 — Newsletter, in two parts

**6a. At launch — store sign-ups ourselves.** One command, so nobody who signs
up in the first week or two is lost while MailerLite is being set up:

```bash
npx wrangler kv namespace create NEWSLETTER
```

Paste the printed id into the commented `kv_namespaces` block in
`wrangler.jsonc`, uncomment those lines, `npx wrangler deploy`. Test the footer
form on the workers.dev address, then `node tools/export_subscribers.mjs`
should show your test address.

Do this **even though** MailerLite is coming: it costs one command, and it is
what catches sign-ups during the changeover. The code prefers the provider as
soon as one is fully configured, and falls back to this storage whenever the
provider is named but its key hasn't been deployed yet — so there is no window
where an address is turned away.

**6b. The CSV route — chosen 25 Aug 2026, and it needs no work.** Sign-ups sit
in KV; when there is a reason to mail them, export and upload:

```bash
node tools/export_subscribers.mjs --since 2026-09-01
```

`--since` makes it incremental, so each export holds only what is new. This is
deliberately *not* the CSV loop that was rejected earlier — that one meant
staying on Squarespace with no API to ever escape to. This one is a holding
pattern with 6c waiting behind it whenever it is wanted.

The reason to sit here for a while: **campaign templates do not transfer.**
Whatever provider is chosen, the layout, branding and footer have to be built
there from scratch. That work gates the first send, not the sign-up form, so
there is nothing to gain by wiring the API early.

Two things to know while in this state. New subscribers get no confirmation or
welcome email — nothing is sending yet — so the first thing they hear from
Paititi is whenever the first campaign goes out. And KV is not a mailing list:
export it before it matters, and keep the CSVs.

**6c. Whenever the provider is settled — switch to the API.** No deadline; the
site keeps collecting in the meantime.
1. Sign up (EmailOctopus Pro unless the MailerLite account turns out to exist),
   verify the domain, import the *subscribed* CSV, set the confirmation email
   and the postal footer.
2. Generate an API key and note the list id.
3. Wire it up:
   ```bash
   npx wrangler secret put NEWSLETTER_API_KEY
   ```
   and add to `wrangler.jsonc` under `vars`:
   ```jsonc
   "NEWSLETTER_PROVIDER": "emailoctopus",
   "NEWSLETTER_LIST_ID": "<the list id>"
   ```
   then `npx wrangler deploy`. Order doesn't matter — until both exist,
   sign-ups keep falling back to our own storage rather than failing.
4. Put one real address through the footer form; confirm it lands in the list
   and that the confirmation email arrives.
5. Import the addresses collected in 6a — `node tools/export_subscribers.mjs`
   → upload that CSV to the same list — and the stopgap is done with.

### Step 7 — Switch nameservers (weekday morning)
Squarespace → Domains → paititi-institute.org → DNS → **Nameservers → Use custom nameservers** → replace the four `ns-cloud-*.googledomains.com` with the two Cloudflare ones → Save. Wait 10 min–2 h (up to 24). Cloudflare emails when Active.
**Immediately test email**: send to info@ from a personal address.

### Step 8 — Attach the domain to the site
Cloudflare → Workers & Pages → paititi-institute → Settings → **Domains & Routes → Add → Custom domain** → `paititi-institute.org`, then `www.paititi-institute.org`. Accept replacing the conflicting records. SSL/TLS → **Full (strict)**, **Always Use HTTPS** on. Open https://paititi-institute.org in a private window. Test the contact form and the newsletter link.

### Step 8b — Redirect www to the apex
Attaching both hostnames as custom domains means both serve the same pages, and
the pages carry no `<link rel="canonical">`, so search engines see duplicate
content across two hosts. Squarespace used to 301 `www`; Cloudflare does not.

Neither obvious fix works. A check in `worker.js` only fires on `/api/*` and
paths with no matching asset, because the assets layer serves real pages
directly without invoking the Worker. And a host-to-host rule in `_redirects` is
rejected outright — Workers Assets allows relative URLs only, unlike Pages.

So it is a zone Redirect Rule: **Cloudflare → the zone → Rules → Redirect Rules
→ Create rule**.

```
If:    Hostname equals www.paititi-institute.org
Then:  Dynamic redirect
       Expression:  concat("https://paititi-institute.org", http.request.uri.path)
       Status 301, preserve query string
```

Free plan includes this. The vestigial check in `worker.js` stays as a backstop
for the paths the rule and the assets layer both miss.

### Step 9 — Tidy up (no rush — the plan is paid into 2027)
1. Search Console → Sitemaps → submit `https://paititi-institute.org/sitemap.xml`.
2. Leave the Squarespace **website** subscription alone until close to renewal.
   It costs nothing extra to let it sit there as a fallback, and while it exists
   the rollback in the next section is instant. When renewal approaches:
   Settings → Billing → **disable auto-renew** on the website subscription
   (cleaner than cancelling — it just runs out).
   **Keep** the domain and **keep** Email Campaigns on auto-renew.
3. Only cancel once the exports from Step 1 are safely in Drive.

### If something goes wrong
- Old site / error: wait 30 min; Cloudflare → DNS must have one `@` and one `www` record labelled Worker; delete stray A/CNAMEs.
- Email stopped: Cloudflare → DNS → compare MX + SPF with screenshots, re-add. Senders retry for 48 h.
- Full rollback: Squarespace → Domains → Nameservers → "Use Squarespace nameservers". Old site back within an hour (as long as Step 9 hasn't happened).
- Contact form "temporarily unavailable": Workers & Pages → paititi-institute → Logs shows why.
- `ERR_QUIC_PROTOCOL_ERROR` in Chrome (seen 25 Aug 2026, right after the switch):
  Cloudflare advertises HTTP/3 (`alt-svc: h3`), which Squarespace never did, so
  Chrome now talks QUIC to the site. In the minutes between the zone going Active
  and Universal SSL being issued (cert timestamp 01:47 UTC), a QUIC handshake
  failed on TLS, and Chrome reports that as this error rather than a certificate
  page. Verified afterwards with headless Chrome forced onto QUIC against
  104.21.86.109: every page loads, every closure is code 70 (client cancel).
  First: private window, or chrome://net-internals/#dns → Clear host cache, plus
  `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder` — the router
  was still handing out Squarespace's 198.49.23.144 with TTL 0 hours later.
  If it persists for anyone on any network: Cloudflare → the zone → Speed →
  Settings → Protocol Optimization → **HTTP/3 (with QUIC) → Off**. Chrome then
  stays on HTTP/2; nothing on this site needs HTTP/3.

## Order in one line
Export the list → screenshot DNS → add domain to Cloudflare → deploy to test address → Resend key → newsletter KV → switch nameservers, check email → attach domain → sitemap. Newsletter provider whenever — nothing waits on it. The Squarespace website itself can keep running until its plan lapses in 2027.
