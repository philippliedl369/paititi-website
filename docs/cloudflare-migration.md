# Moving paititi-institute.org to Cloudflare

Updated 23 Aug 2026. Decisions so far: Cloudflare account exists; Stripe is not
used; the store is gone. The newsletter cannot stay on Squarespace — it has no
subscribe API, so a new site could only feed it by hand — and choosing its
replacement is the last open question.

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
- **Newsletter list** (needed — this is the list that moves to the new provider): Squarespace → your site → **Marketing → Email Campaigns → Mailing Lists** (newer accounts: **Contacts → Lists & Segments**) → hover the list → **⋯ → Export**. You get a .zip with three CSVs (subscribed / unsubscribed / cleaned). Keep all three.
- **Orders** (the old US Tour RSVP payments — records only, the store is not coming back): **Commerce → Orders** (newer UI: **Products & Services → Orders**) → **Export data → Download CSV**. Pick *All statuses* and the full date range.
- **Contacts** (customers + donors + subscribers in one): **Contacts** panel → **Export**.
- **Form submissions**, if any forms stored responses in Squarespace rather than emailing them: **Contacts**, or the form block's own storage — see **Settings → Form & Newsletter Storage**.
- **DNS screenshots**: Squarespace → **Domains → paititi-institute.org → DNS settings** — screenshot the entire page.

### The newsletter — the one real decision left

**It has to move, and here is why.** Squarespace offers no way for
an outside website to add a subscriber: no API, and its hosted sign-up form is
not findable in this account. Staying on Squarespace therefore means exporting
and importing a CSV by hand forever, which is not a plan. Automations don't
rescue it either — "Tag Contacts who fill out a form" triggers on *"a form
completed on your site"*, meaning the Squarespace site, and Squarespace stops
automations once that site is offline.

So sign-ups go to a provider with an API. `api.js` already speaks six of them
and all six are tested; picking one is three values, no code:

```
NEWSLETTER_PROVIDER   kit | mailerlite | brevo | mailchimp | beehiiv | resend
NEWSLETTER_API_KEY    that provider's key   (secret)
NEWSLETTER_LIST_ID    the form / group / list / audience id
```

**Check this first.** The domain's DNS already carries a MailerLite SPF include
(`include:_spf.mlsend.com`) and a Brevo verification code. An SPF include means
someone actually configured *sending* through MailerLite at some point. If that
account exists and holds the list, it is the obvious answer — no new account,
DNS already correct, and MailerLite is one of the six. Find out who set it up
before choosing anything else.

**If nothing usable exists, the choice comes down to list size** (the Squarespace
export in Step 1 tells you):

| | Free tier | Good for | Watch out |
|---|---|---|---|
| **Kit** (recommended) | 10,000 subscribers, unlimited sends | Almost certainly covers this list at no cost | Kit branding on emails; 1 form, 1 automation |
| **Brevo** | Unlimited contacts, 300 emails/**day** | Small lists | A 2,000-person send takes a week on free. Realistically $9/mo |
| **MailerLite** | 250 subscribers (cut from 500 in June 2026) | Only if the account already exists and is paid | $12/mo for 500 |

Whichever it is, do these three in the provider, not here: **verify the domain
with SPF/DKIM/DMARC while we still control DNS**, set the confirmation email
(new sign-ups double opt in by default), and put the postal address in the
campaign footer — bulk email legally needs it, and Squarespace used to supply it
invisibly.

**Import the old list** into the new provider from the Step 1 CSV. Import only
the *subscribed* file; the unsubscribed and cleaned files exist so you can
honour those opt-outs, not re-mail them.

### The store — removed 23 Aug 2026
Nothing was sold there but the US Tour RSVP donation, for an event that has
passed. Retreats and online courses book through Retreat Guru, and donations go
through Zeffy, so no cart is needed. The pages are deleted; `/store`,
`/store/*`, `/cart` and `/order-confirmed` now 301 to Programs and home so old
links and Google results don't hit a dead end. Recoverable from git if a shop is
ever wanted. No Stripe key is needed for anything on the new site.

### DNS records that must survive (snapshot 22 Aug 2026)
```
MX   @  1  aspmx.l.google.com.           ← Google Workspace email — critical
MX   @  5  alt1.aspmx.l.google.com.
MX   @  5  alt2.aspmx.l.google.com.
MX   @  10 alt3.aspmx.l.google.com.
MX   @  10 alt4.aspmx.l.google.com.
TXT  @  v=spf1 a mx include:_spf.mlsend.com ~all
TXT  @  google-site-verification=ivzXeym1DKcL_IvbRLC1VfM59qfEsHnv5lwseX-1kMs
TXT  @  google-site-verification=JQ0U4i7LILgU_tP2BCaFJRzhGQSWmVQvg-Kj9mtLLYo
TXT  @  google-site-verification=1o32nOtx_4Y5fJ18bf9sTxbY27yOpsMMSK-a21WBNZo
TXT  @  brevo-code:268dfc87244d85fd7b18362e4bf8f193
TXT  @  mailerlite-domain-verification=946625c1545d080d6432144ea8f498b5c06525b8
```
Records pointing at Squarespace (`A 198.185.159.x / 198.49.23.x`, `www → ext-sq.squarespace.com`) are the ones we replace. There may be more records (DKIM, subdomains) — the screenshots are the source of truth.

### Secrets the site needs
Two: `RESEND_API_KEY` (contact form) and `NEWSLETTER_API_KEY` (whichever
provider wins), plus the plain variables `NEWSLETTER_PROVIDER` and
`NEWSLETTER_LIST_ID`. Missing either one only disables that one form — it says
"temporarily unavailable" and logs the real reason; the rest of the site works.

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

### Step 6 — Newsletter provider
1. Settle the provider question above (start by finding out who owns the
   MailerLite account the DNS points at).
2. In that provider: verify the domain, import the Step 1 CSV, create the list,
   generate an API key, note the list/form id.
3. Set the three values — key as a secret, the other two as plain variables:
   ```bash
   npx wrangler secret put NEWSLETTER_API_KEY
   ```
   `NEWSLETTER_PROVIDER` and `NEWSLETTER_LIST_ID` go in `wrangler.jsonc` under
   `vars` (or the dashboard), then `npx wrangler deploy`.
4. Put one real address through the footer form and confirm it arrives.

**Safety net, if the provider isn't settled by launch:** create the KV
namespace instead and the form keeps every address rather than turning people
away —

```bash
npx wrangler kv namespace create NEWSLETTER
```

paste the printed id into the commented `kv_namespaces` block in
`wrangler.jsonc`, uncomment, deploy. `node tools/export_subscribers.mjs` reads
them back out later for a one-time import into whichever provider wins. This is
a stopgap, not a destination: a stored address with nothing to send from it is
not a newsletter.

### Step 7 — Switch nameservers (weekday morning)
Squarespace → Domains → paititi-institute.org → DNS → **Nameservers → Use custom nameservers** → replace the four `ns-cloud-*.googledomains.com` with the two Cloudflare ones → Save. Wait 10 min–2 h (up to 24). Cloudflare emails when Active.
**Immediately test email**: send to info@ from a personal address.

### Step 8 — Attach the domain to the site
Cloudflare → Workers & Pages → paititi-institute → Settings → **Domains & Routes → Add → Custom domain** → `paititi-institute.org`, then `www.paititi-institute.org`. Accept replacing the conflicting records. SSL/TLS → **Full (strict)**, **Always Use HTTPS** on. Open https://paititi-institute.org in a private window. Test the contact form and the newsletter link.

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

## Order in one line
Export the list → screenshot DNS → add domain to Cloudflare → deploy to test address → Resend key → pick the newsletter provider and import the list → switch nameservers, check email → attach domain → sitemap. The Squarespace website itself can keep running until its plan lapses in 2027.
