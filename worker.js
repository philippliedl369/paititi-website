/**
 * Paititi Institute — Worker backend.
 * Replaces the functions Squarespace used to provide:
 *   POST /api/contact     — contact form → email via Resend (RESEND_API_KEY)
 *   POST /api/newsletter  — newsletter signup → KV list (NEWSLETTER binding)
 *                           + optional forward to Resend audience
 *   POST /api/checkout    — cart/donation → Stripe Checkout session
 *                           (STRIPE_SECRET_KEY); items are validated against
 *                           /data/products.json so prices can't be tampered with
 * Everything else falls through to the static assets (ASSETS binding).
 *
 * Secrets (set with `npx wrangler secret put <NAME>`):
 *   RESEND_API_KEY     — transactional email (contact form, notifications)
 *   STRIPE_SECRET_KEY  — Stripe secret key (sk_live_… / sk_test_…)
 * Vars (wrangler.jsonc → "vars"):
 *   CONTACT_TO         — inbox that receives contact-form submissions
 *   SITE_ORIGIN        — canonical origin used in Stripe success/cancel URLs
 */

const JSON_HEADERS = { 'content-type': 'application/json' };

const ok = (data) => new Response(JSON.stringify(data), { headers: JSON_HEADERS });
const err = (status, message) =>
  new Response(JSON.stringify({ error: message }), { status, headers: JSON_HEADERS });

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname.startsWith('/api/')) {
      try {
        return await handleApi(request, env, url);
      } catch (e) {
        console.error('api error', url.pathname, e);
        return err(500, 'Internal error');
      }
    }
    return env.ASSETS.fetch(request);
  },
};

async function handleApi(request, env, url) {
  if (request.method !== 'POST') return err(405, 'Method not allowed');
  const body = await request.json().catch(() => null);
  if (!body) return err(400, 'Invalid JSON body');

  // Honeypot: real forms include an empty "website" field; bots fill it.
  if (typeof body.website === 'string' && body.website.trim() !== '') return ok({ ok: true });

  switch (url.pathname) {
    case '/api/contact':
      return contact(body, env);
    case '/api/newsletter':
      return newsletter(body, env);
    case '/api/checkout':
      return checkout(body, env, url);
    default:
      return err(404, 'Not found');
  }
}

/* ---------------- contact form ---------------- */

async function contact(body, env) {
  const { name, email, subject, message } = body;
  if (!name || !email || !message) return err(400, 'name, email and message are required');
  if (!isEmail(email)) return err(400, 'Invalid email address');
  if (!env.RESEND_API_KEY) return err(503, 'Contact form not configured yet (RESEND_API_KEY)');

  const to = env.CONTACT_TO || 'info@paititi-institute.org';
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { ...JSON_HEADERS, authorization: `Bearer ${env.RESEND_API_KEY}` },
    body: JSON.stringify({
      from: 'Website <website@paititi-institute.org>',
      to: [to],
      reply_to: email,
      subject: `[Website contact] ${subject || 'New message'} — ${name}`,
      text: `Name: ${name}\nEmail: ${email}\n\n${message}`,
    }),
  });
  if (!res.ok) {
    console.error('resend failed', res.status, await res.text());
    return err(502, 'Could not send message, please email us directly.');
  }
  return ok({ ok: true });
}

/* ---------------- newsletter ---------------- */

async function newsletter(body, env) {
  const email = (body.email || '').trim().toLowerCase();
  if (!isEmail(email)) return err(400, 'Invalid email address');
  if (env.NEWSLETTER) {
    await env.NEWSLETTER.put(email, JSON.stringify({ ts: new Date().toISOString(), source: body.source || 'site' }));
  } else if (env.RESEND_API_KEY && env.RESEND_AUDIENCE_ID) {
    const res = await fetch(`https://api.resend.com/audiences/${env.RESEND_AUDIENCE_ID}/contacts`, {
      method: 'POST',
      headers: { ...JSON_HEADERS, authorization: `Bearer ${env.RESEND_API_KEY}` },
      body: JSON.stringify({ email, unsubscribed: false }),
    });
    if (!res.ok) return err(502, 'Signup failed, please try again later.');
  } else {
    return err(503, 'Newsletter not configured yet (NEWSLETTER KV or Resend audience)');
  }
  return ok({ ok: true });
}

/* ---------------- checkout (store, retreats, donations) ---------------- */

async function checkout(body, env, url) {
  if (!env.STRIPE_SECRET_KEY) return err(503, 'Checkout not configured yet (STRIPE_SECRET_KEY)');
  const items = Array.isArray(body.items) ? body.items : [];
  if (items.length === 0) return err(400, 'Cart is empty');

  // Load the trusted catalog from static assets.
  const origin = env.SITE_ORIGIN || url.origin;
  const catalogRes = await env.ASSETS.fetch(new Request(`${origin}/data/products.json`));
  if (!catalogRes.ok) return err(500, 'Product catalog unavailable');
  const catalog = await catalogRes.json();
  const byId = Object.fromEntries(catalog.products.map((p) => [p.id, p]));

  // Recurring donations (the Squarespace donation block offered weekly …
  // yearly) map onto Stripe subscription mode.
  const INTERVALS = {
    weekly: ['week', 1], monthly: ['month', 1], quarterly: ['month', 3], yearly: ['year', 1],
  };
  const recurring = items.some((it) => INTERVALS[it.frequency]);
  const params = new URLSearchParams();
  params.set('mode', recurring ? 'subscription' : 'payment');
  params.set('success_url', `${origin}/order-confirmed?session_id={CHECKOUT_SESSION_ID}`);
  params.set('cancel_url', `${origin}/cart`);
  let i = 0;
  for (const item of items) {
    const p = byId[item.id];
    if (!p) return err(400, `Unknown product: ${item.id}`);
    let amountCents;
    if (p.customAmount) {
      // Donations: client supplies the amount, but never below the product minimum.
      amountCents = Math.round(Number(item.amount) * 100);
      if (!Number.isFinite(amountCents) || amountCents < (p.minAmountCents || 100)) {
        return err(400, `Invalid amount for ${p.name}`);
      }
    } else if (item.variantId) {
      const v = (p.variants || []).find((v) => v.id === item.variantId);
      if (!v) return err(400, `Unknown variant for ${p.name}`);
      amountCents = v.priceCents;
    } else {
      amountCents = p.priceCents;
    }
    const qty = Math.max(1, Math.min(20, parseInt(item.qty, 10) || 1));
    params.set(`line_items[${i}][price_data][currency]`, p.currency || 'usd');
    params.set(`line_items[${i}][price_data][product_data][name]`, p.name + (item.variantId ? ` — ${item.variantId}` : ''));
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
    return err(502, 'Checkout failed, please try again.');
  }
  return ok({ url: session.url });
}

function isEmail(s) {
  return typeof s === 'string' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
}
