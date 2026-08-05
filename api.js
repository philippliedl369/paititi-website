/**
 * Paititi Institute — API handlers, shared by both deployment targets.
 *
 * The site runs either on Cloudflare Workers (worker.js) or on a plain Node
 * host such as Railway (server.js). Both adapters delegate here so the
 * business logic — validation, Stripe line items, price checking — exists
 * once and cannot drift between platforms.
 *
 * Everything below is platform-agnostic: no Cloudflare bindings, no Node
 * built-ins. The adapters inject what differs via `deps`:
 *   readCatalog() -> the parsed data/products.json
 *   saveSubscriber(email, meta) -> persist a newsletter signup, or null
 */

export const JSON_HEADERS = { 'content-type': 'application/json' };

const ok = (data) => ({ status: 200, body: data });
const fail = (status, message) => ({ status, body: { error: message } });

/**
 * A failure whose cause is ours, not the visitor's. The reason goes to the
 * log; the response carries copy written for the person standing in front of
 * the form. The forms print `error` verbatim, so nothing internal — missing
 * secrets, provider names, product ids — may travel in it.
 */
function unavailable(cause, message) {
  console.error('[paititi]', cause);
  return fail(503, message);
}

export function isEmail(s) {
  return typeof s === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
}

/**
 * Route one API request.
 * @returns {{status:number, body:object}}
 */
export async function handleApi({ method, pathname, body, env, origin, deps }) {
  if (method !== 'POST') return fail(405, 'Method not allowed');
  if (!body || typeof body !== 'object') return fail(400, 'Invalid JSON body');

  // Honeypot: the real forms ship an empty "website" field; bots fill it in.
  // Answer 200 so the bot believes it succeeded.
  if (typeof body.website === 'string' && body.website.trim() !== '') {
    return ok({ ok: true });
  }

  switch (pathname) {
    case '/api/contact':
      return contact(body, env, deps);
    case '/api/newsletter':
      return newsletter(body, env, deps);
    case '/api/checkout':
      return checkout(body, env, origin, deps);
    default:
      return fail(404, 'Not found');
  }
}

/* ---------------- contact form ---------------- */

async function contact(body, env, deps) {
  const { name, email, subject, message } = body;
  if (!name || !email || !message) return fail(400, 'name, email and message are required');
  if (!isEmail(email)) return fail(400, 'Invalid email address');
  const to = env.CONTACT_TO || 'info@paititi-institute.org';
  if (!env.RESEND_API_KEY) {
    return unavailable('contact: RESEND_API_KEY is not set',
      `This form is temporarily unavailable — please email us at ${to}.`);
  }

  const from = env.CONTACT_FROM || 'Website <website@paititi-institute.org>';
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { ...JSON_HEADERS, authorization: `Bearer ${env.RESEND_API_KEY}` },
    body: JSON.stringify({
      from,
      to: [to],
      reply_to: email,
      subject: `[Website contact] ${subject || 'New message'} — ${name}`,
      text: `Name: ${name}\nEmail: ${email}\n\n${message}`,
    }),
  });
  if (!res.ok) {
    console.error('resend failed', res.status, await res.text());
    return fail(502, 'Could not send message, please email us directly.');
  }
  return ok({ ok: true });
}

/* ---------------- newsletter ----------------
 * Both the list and the sending used to live in Squarespace. Whichever email
 * provider replaces it, the site itself only ever makes one call — add this
 * address to that list — so the provider is a table entry rather than a branch
 * through the handler. Switching is three environment values:
 *
 *   NEWSLETTER_PROVIDER   one of the keys below
 *   NEWSLETTER_API_KEY    that provider's key
 *   NEWSLETTER_LIST_ID    the audience / list / form / publication to join
 *
 * Composing and sending campaigns stays in the provider's own tooling; this
 * file is only the subscribe hook. Unsubscribe links, the postal address and
 * the confirmation email are the provider's job too, and are not optional —
 * Squarespace supplied all three invisibly.
 *
 * These are each provider's documented add-subscriber call, but mail APIs
 * version: check the current docs for whichever you pick, and put one real
 * signup through it before launch.
 */
const NEWSLETTER_PROVIDERS = {
  // Mailchimp keys carry their datacenter after the final hyphen — abc123…-us21.
  mailchimp: (email, env, confirm) => ({
    url: `https://${env.NEWSLETTER_API_KEY.split('-').pop() || 'us1'}.api.mailchimp.com/3.0`
       + `/lists/${env.NEWSLETTER_LIST_ID}/members`,
    headers: { authorization: `Bearer ${env.NEWSLETTER_API_KEY}` },
    body: { email_address: email, status: confirm ? 'pending' : 'subscribed' },
  }),
  // Kit (formerly ConvertKit): LIST_ID is a form id, and the form's own
  // setting decides whether it double opts in.
  kit: (email, env) => ({
    url: `https://api.kit.com/v4/forms/${env.NEWSLETTER_LIST_ID}/subscribers`,
    headers: { 'X-Kit-Api-Key': env.NEWSLETTER_API_KEY },
    body: { email_address: email },
  }),
  mailerlite: (email, env) => ({
    url: 'https://connect.mailerlite.com/api/subscribers',
    headers: { authorization: `Bearer ${env.NEWSLETTER_API_KEY}`, accept: 'application/json' },
    body: { email, groups: [env.NEWSLETTER_LIST_ID] },
  }),
  // Brevo confirms through a separate double-opt-in endpoint that needs its own
  // template id, so set confirmation up in Brevo rather than expecting it here.
  brevo: (email, env) => ({
    url: 'https://api.brevo.com/v3/contacts',
    headers: { 'api-key': env.NEWSLETTER_API_KEY },
    body: { email, listIds: [Number(env.NEWSLETTER_LIST_ID)], updateEnabled: true },
  }),
  beehiiv: (email, env) => ({
    url: `https://api.beehiiv.com/v2/publications/${env.NEWSLETTER_LIST_ID}/subscriptions`,
    headers: { authorization: `Bearer ${env.NEWSLETTER_API_KEY}` },
    body: { email, send_welcome_email: true, utm_source: 'paititi-institute.org' },
  }),
  resend: (email, env) => ({
    url: `https://api.resend.com/audiences/${env.NEWSLETTER_LIST_ID}/contacts`,
    headers: { authorization: `Bearer ${env.NEWSLETTER_API_KEY}` },
    body: { email, unsubscribed: false },
  }),
};

// Signing up twice is not an error worth showing anyone.
const ALREADY_SUBSCRIBED = /already|exists|duplicate/i;

async function newsletter(body, env, deps) {
  const email = (body.email || '').trim().toLowerCase();
  if (!isEmail(email)) return fail(400, 'Invalid email address');

  const soon = 'Sign-up is temporarily unavailable — please try again shortly.';

  const name = env.NEWSLETTER_PROVIDER
    // Carried over from the pre-provider build, where signups went to a Resend
    // audience under its own variable names.
    || (env.RESEND_API_KEY && env.RESEND_AUDIENCE_ID ? 'resend' : '');
  const build = NEWSLETTER_PROVIDERS[name];

  if (build) {
    const key = env.NEWSLETTER_API_KEY || env.RESEND_API_KEY;
    const list = env.NEWSLETTER_LIST_ID || env.RESEND_AUDIENCE_ID;
    if (!key || !list) {
      return unavailable(`newsletter: ${name} selected but API key or list id is missing`, soon);
    }
    // Default to double opt-in: the list is being rebuilt on a cold sending
    // domain, and confirmed addresses are what keep it out of spam folders.
    const confirm = env.NEWSLETTER_DOUBLE_OPT_IN !== 'false';
    const req = build(email, { ...env, NEWSLETTER_API_KEY: key, NEWSLETTER_LIST_ID: list }, confirm);
    const res = await fetch(req.url, {
      method: 'POST',
      headers: { ...JSON_HEADERS, ...req.headers },
      body: JSON.stringify(req.body),
    });
    if (!res.ok) {
      const detail = await res.text().catch(() => '');
      if (res.status < 500 && ALREADY_SUBSCRIBED.test(detail)) return ok({ ok: true });
      console.error('[paititi] newsletter:', name, res.status, detail.slice(0, 300));
      return fail(502, soon);
    }
    return ok({ ok: true });
  }

  // No provider yet. Keep the address rather than dropping it, but only where
  // the host offers storage — a bare list with nothing to send from it is not
  // a newsletter, so this is a stopgap and not a destination.
  if (deps.saveSubscriber) {
    await deps.saveSubscriber(email, { ts: new Date().toISOString(), source: body.source || 'site' });
    return ok({ ok: true });
  }
  return unavailable('newsletter: no NEWSLETTER_PROVIDER configured and no storage bound', soon);
}

/* ---------------- checkout (store, retreats, donations) ---------------- */

// The Squarespace donation block offered weekly…annually; these map onto
// Stripe subscription intervals.
const INTERVALS = {
  weekly: ['week', 1],
  monthly: ['month', 1],
  quarterly: ['month', 3],
  yearly: ['year', 1],
};

async function checkout(body, env, origin, deps) {
  const soon = 'Checkout is temporarily unavailable — please try again shortly.';
  if (!env.STRIPE_SECRET_KEY) {
    return unavailable('checkout: STRIPE_SECRET_KEY is not set', soon);
  }
  const items = Array.isArray(body.items) ? body.items : [];
  if (items.length === 0) return fail(400, 'Cart is empty');

  let catalog;
  try {
    catalog = await deps.readCatalog();
  } catch (e) {
    console.error('[paititi] checkout: catalog unavailable', e);
    return fail(500, soon);
  }
  const byId = Object.fromEntries(catalog.products.map((p) => [p.id, p]));

  const recurring = items.some((it) => INTERVALS[it.frequency]);
  const params = new URLSearchParams();
  params.set('mode', recurring ? 'subscription' : 'payment');
  params.set('success_url', `${origin}/order-confirmed?session_id={CHECKOUT_SESSION_ID}`);
  params.set('cancel_url', `${origin}/cart`);

  let i = 0;
  for (const item of items) {
    const p = byId[item.id];
    if (!p) {
      console.error('[paititi] checkout: unknown product', item.id);
      return fail(400, 'One of the items in your cart is no longer available.');
    }

    // Prices always come from the catalog, never from the client — the only
    // client-supplied amount is a donation, and it is floor-checked.
    let amountCents;
    if (p.customAmount) {
      amountCents = Math.round(Number(item.amount) * 100);
      if (!Number.isFinite(amountCents) || amountCents < (p.minAmountCents || 100)) {
        return fail(400, `Invalid amount for ${p.name}`);
      }
    } else if (item.variantId) {
      const v = (p.variants || []).find((v) => v.id === item.variantId);
      if (!v) {
        console.error('[paititi] checkout: unknown variant', item.variantId, 'of', p.id);
        return fail(400, `The option you chose for ${p.name} is no longer available.`);
      }
      amountCents = v.priceCents;
    } else {
      amountCents = p.priceCents;
    }

    const qty = Math.max(1, Math.min(20, parseInt(item.qty, 10) || 1));
    const name = p.name + (item.variantId ? ` — ${item.variantId}` : '');
    params.set(`line_items[${i}][price_data][currency]`, p.currency || 'usd');
    params.set(`line_items[${i}][price_data][product_data][name]`, name);
    params.set(`line_items[${i}][price_data][unit_amount]`, String(amountCents));
    if (INTERVALS[item.frequency]) {
      const [interval, count] = INTERVALS[item.frequency];
      params.set(`line_items[${i}][price_data][recurring][interval]`, interval);
      params.set(`line_items[${i}][price_data][recurring][interval_count]`, String(count));
    }
    params.set(`line_items[${i}][quantity]`, String(qty));
    i++;
  }

  const res = await fetch('https://api.stripe.com/v1/checkout/sessions', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
      'content-type': 'application/x-www-form-urlencoded',
    },
    body: params,
  });
  const session = await res.json();
  if (!res.ok) {
    console.error('stripe failed', res.status, JSON.stringify(session.error || session));
    return fail(502, 'Checkout failed, please try again.');
  }
  return ok({ url: session.url });
}
