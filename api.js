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
  if (!env.RESEND_API_KEY) return fail(503, 'Contact form not configured yet (RESEND_API_KEY)');

  const to = env.CONTACT_TO || 'info@paititi-institute.org';
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

/* ---------------- newsletter ---------------- */

async function newsletter(body, env, deps) {
  const email = (body.email || '').trim().toLowerCase();
  if (!isEmail(email)) return fail(400, 'Invalid email address');

  const meta = { ts: new Date().toISOString(), source: body.source || 'site' };

  if (deps.saveSubscriber) {
    await deps.saveSubscriber(email, meta);
    return ok({ ok: true });
  }
  if (env.RESEND_API_KEY && env.RESEND_AUDIENCE_ID) {
    const res = await fetch(
      `https://api.resend.com/audiences/${env.RESEND_AUDIENCE_ID}/contacts`,
      {
        method: 'POST',
        headers: { ...JSON_HEADERS, authorization: `Bearer ${env.RESEND_API_KEY}` },
        body: JSON.stringify({ email, unsubscribed: false }),
      });
    if (!res.ok) return fail(502, 'Signup failed, please try again later.');
    return ok({ ok: true });
  }
  return fail(503, 'Newsletter not configured yet (storage or Resend audience)');
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
  if (!env.STRIPE_SECRET_KEY) return fail(503, 'Checkout not configured yet (STRIPE_SECRET_KEY)');
  const items = Array.isArray(body.items) ? body.items : [];
  if (items.length === 0) return fail(400, 'Cart is empty');

  let catalog;
  try {
    catalog = await deps.readCatalog();
  } catch (e) {
    console.error('catalog unavailable', e);
    return fail(500, 'Product catalog unavailable');
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
    if (!p) return fail(400, `Unknown product: ${item.id}`);

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
      if (!v) return fail(400, `Unknown variant for ${p.name}`);
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
