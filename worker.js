/**
 * Cloudflare Workers adapter.
 *
 * Serves the repo as static assets and hands /api/* to the shared handlers in
 * api.js (the same ones server.js uses on Railway). Deploy with `wrangler deploy`.
 *
 * Secrets (npx wrangler secret put <NAME>):
 *   RESEND_API_KEY     — transactional email for the contact form
 *   STRIPE_SECRET_KEY  — store and donation checkout
 *   NEWSLETTER_API_KEY — the email provider that replaced Squarespace campaigns
 * Vars (wrangler.jsonc -> "vars"):
 *   CONTACT_TO         — inbox that receives contact-form submissions
 *   SITE_ORIGIN        — canonical origin for Stripe success/cancel URLs
 *   NEWSLETTER_PROVIDER / NEWSLETTER_LIST_ID — see api.js
 * Optional: a KV namespace bound as NEWSLETTER holds signups until a provider
 * is chosen, so addresses collected in the meantime are not simply dropped.
 */
import { handleApi, JSON_HEADERS } from './api.js';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith('/api/')) {
      const res = await env.ASSETS.fetch(request);
      // The workers.dev preview host does get crawled, and an indexed preview
      // would compete with paititi-institute.org after the DNS switch. The
      // header covers every page and asset without touching the HTML.
      if (url.hostname.endsWith('.workers.dev')) {
        const headers = new Headers(res.headers);
        headers.set('X-Robots-Tag', 'noindex');
        return new Response(res.body, { status: res.status, statusText: res.statusText, headers });
      }
      return res;
    }

    const origin = env.SITE_ORIGIN || url.origin;
    let body = null;
    if (request.method === 'POST') {
      body = await request.json().catch(() => null);
    }

    try {
      const { status, body: payload } = await handleApi({
        method: request.method,
        pathname: url.pathname,
        body,
        env,
        origin,
        deps: {
          readCatalog: async () => {
            const res = await env.ASSETS.fetch(new Request(`${origin}/data/products.json`));
            if (!res.ok) throw new Error(`catalog ${res.status}`);
            return res.json();
          },
          // Present only when a KV namespace is bound; otherwise api.js falls
          // back to the Resend audience.
          saveSubscriber: env.NEWSLETTER
            ? (email, meta) => env.NEWSLETTER.put(email, JSON.stringify(meta))
            : null,
        },
      });
      return new Response(JSON.stringify(payload), { status, headers: JSON_HEADERS });
    } catch (e) {
      console.error('api error', url.pathname, e);
      return new Response(JSON.stringify({ error: 'Internal error' }), {
        status: 500, headers: JSON_HEADERS,
      });
    }
  },
};
