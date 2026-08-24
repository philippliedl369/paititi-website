# Moving paititi-institute.org to Cloudflare

Updated 23 Aug 2026. Decisions so far: Cloudflare account exists; Stripe is not
used; the store is gone; the newsletter stays on Squarespace Email Campaigns
for now.

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
- **Newsletter list**: Squarespace → your site → **Marketing → Email Campaigns → Mailing Lists** (newer accounts: **Contacts → Lists & Segments**) → hover the list → **⋯ → Export**. You get a .zip with three CSVs (subscribed / unsubscribed / cleaned). Keep all three.
- **Orders** (the old US Tour RSVP payments — records only, the store is not coming back): **Commerce → Orders** (newer UI: **Products & Services → Orders**) → **Export data → Download CSV**. Pick *All statuses* and the full date range.
- **Contacts** (customers + donors + subscribers in one): **Contacts** panel → **Export**.
- **Form submissions**, if any forms stored responses in Squarespace rather than emailing them: **Contacts**, or the form block's own storage — see **Settings → Form & Newsletter Storage**.
- **DNS screenshots**: Squarespace → **Domains → paititi-institute.org → DNS settings** — screenshot the entire page.

### The newsletter plan (stays on Squarespace)
Squarespace says: *"Billing for Email Campaigns is separate from your site
subscription. If you cancel your site subscription, or let it expire, we won't
turn off auto-renew for an existing Email Campaigns subscription, and you can
continue using it."* Manual campaigns keep sending; only **automations** (e.g.
welcome emails) stop once the site is gone.

So the list, the sending, the unsubscribe footer — all stay where they are.
Two things change:

**Sign-ups from the new site: nothing to find in Squarespace.** Squarespace has
no subscribe API, and its "Sign-up forms" panel is proving hard to locate —
so we don't use it. The site keeps its own newsletter box in the footer, and
Cloudflare stores the addresses (`api.js` → KV). Setup is one command, in
Step 6 below.

Getting those addresses into Squarespace so campaigns can go out is then a
two-minute job whenever you feel like it:

```bash
node tools/export_subscribers.mjs              # → subscribers-YYYY-MM-DD.csv
node tools/export_subscribers.mjs --since 2026-09-01   # only what's new
```

Then Squarespace → **Lists & Segments** → the list → **Add Subscribers →
Upload a list** → choose the CSV → switch on *"These subscribers accept
marketing"* → **Import**.

**Do NOT use Automations for this.** The "Tag Contacts who fill out a form"
automation triggers on *"a form completed on your site"* — the Squarespace
site, which is the thing going away. Squarespace stops automations once the
site is offline, so anything built there is temporary by definition. If
Automations already holds something live, note what it does; an empty list
means nothing to do.

**The shortcut worth considering.** The domain's DNS already carries a
MailerLite SPF include *and* a Brevo verification code, so an account at one or
both already exists. If either one holds (or could hold) the list, sign-ups
flow automatically with no CSV ever — `api.js` speaks both. It needs three
values, and the manual step disappears:

```
NEWSLETTER_PROVIDER   mailerlite | brevo
NEWSLETTER_API_KEY    that provider's key   (secret)
NEWSLETTER_LIST_ID    the group / list id
```

Worth ten minutes finding out who set those up before committing to the
monthly CSV.

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
Only one now: `RESEND_API_KEY` (contact form). Without it the contact form says
"temporarily unavailable"; everything else works.

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

### Step 6 — Newsletter storage
One command, so the footer sign-up box has somewhere to put an address:

```bash
npx wrangler kv namespace create NEWSLETTER
```

It prints an id. Paste it into `wrangler.jsonc` (the commented `kv_namespaces`
block near the bottom shows exactly where), uncomment those lines, then
`npx wrangler deploy`. Test the sign-up box on the workers.dev address; then
`node tools/export_subscribers.mjs` should show your test address.

Skip this only if you go the MailerLite/Brevo route above — then set the three
`NEWSLETTER_*` values instead and no KV is needed.

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
Screenshot DNS → add domain to Cloudflare → deploy to test address → Resend key → newsletter KV → switch nameservers, check email → attach domain → sitemap. Exports any time before the eventual website cancellation, which can wait until the plan runs out in 2027.
