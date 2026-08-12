/**
 * Node adapter — for Railway, Render, Fly, or any plain Node host.
 *
 * Cloudflare gives us three things for free that a generic Node host does not:
 * clean-URL rewrites (_redirects), response headers (_headers), and the Worker
 * that answers /api/*. This server reproduces all three against the very same
 * files, so one repo deploys to either platform with no content changes.
 *
 *   node server.js            # PORT defaults to 8080
 *
 * Environment (Railway → Variables):
 *   RESEND_API_KEY, STRIPE_SECRET_KEY, CONTACT_TO, SITE_ORIGIN,
 *   RESEND_AUDIENCE_ID (newsletter), NEWSLETTER_FILE (optional, see below)
 */
import { createServer } from 'node:http';
import { readFile, appendFile, stat } from 'node:fs/promises';
import { createReadStream } from 'node:fs';
import { join, normalize, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { handleApi, JSON_HEADERS } from './api.js';

const ROOT = fileURLToPath(new URL('.', import.meta.url));
const PORT = process.env.PORT || 8080;

const MIME = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.webp': 'image/webp', '.gif': 'image/gif', '.ico': 'image/x-icon',
  '.pdf': 'application/pdf', '.woff2': 'font/woff2', '.woff': 'font/woff',
  '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml; charset=utf-8',
  '.webmanifest': 'application/manifest+json',
};

/* ---------- _redirects: "<from> <to> <status>", one rule per line ---------- */

async function loadRedirects() {
  let text = '';
  try {
    text = await readFile(join(ROOT, '_redirects'), 'utf8');
  } catch {
    return [];
  }
  const rules = [];
  for (const line of text.split('\n')) {
    const s = line.trim();
    if (!s || s.startsWith('#')) continue;
    const [from, to, code] = s.split(/\s+/);
    if (!from || !to) continue;
    rules.push({ from, to, status: parseInt(code, 10) || 200 });
  }
  return rules;
}

/* ---------- _headers: a path block, then indented "Name: value" lines ---------- */

async function loadHeaders() {
  let text = '';
  try {
    text = await readFile(join(ROOT, '_headers'), 'utf8');
  } catch {
    return [];
  }
  const blocks = [];
  let current = null;
  for (const line of text.split('\n')) {
    if (!line.trim() || line.trim().startsWith('#')) continue;
    if (!/^\s/.test(line)) {
      current = { pattern: line.trim(), headers: {} };
      blocks.push(current);
    } else if (current) {
      const idx = line.indexOf(':');
      if (idx > 0) {
        current.headers[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
      }
    }
  }
  return blocks;
}

function headersFor(pathname, blocks) {
  const out = {};
  for (const b of blocks) {
    const p = b.pattern;
    const match = p === '/*' || p === pathname ||
      (p.endsWith('/*') && pathname.startsWith(p.slice(0, -1)));
    if (match) Object.assign(out, b.headers);
  }
  return out;
}

/* ---------- static files ---------- */

async function resolveFile(pathname) {
  // normalize() collapses any ../ before we touch the filesystem.
  const rel = normalize(decodeURIComponent(pathname)).replace(/^(\.\.[/\\])+/, '');
  const abs = join(ROOT, rel);
  if (!abs.startsWith(ROOT)) return null;          // escaped the web root
  try {
    const st = await stat(abs);
    if (st.isFile()) return { abs, size: st.size };
    if (st.isDirectory()) {
      const index = join(abs, 'index.html');
      const ist = await stat(index).catch(() => null);
      if (ist?.isFile()) return { abs: index, size: ist.size };
    }
  } catch { /* not found */ }
  return null;
}

const send = (res, status, headers, body) => {
  res.writeHead(status, headers);
  res.end(body);
};

/* ---------- newsletter storage (no KV outside Cloudflare) ---------- */

// Railway containers have an ephemeral filesystem: without a mounted volume
// this file disappears on redeploy. Prefer RESEND_AUDIENCE_ID in production;
// NEWSLETTER_FILE is here for self-hosting with a persistent volume.
const NEWSLETTER_FILE = process.env.NEWSLETTER_FILE;
const saveSubscriber = NEWSLETTER_FILE
  ? (email, meta) => appendFile(NEWSLETTER_FILE, JSON.stringify({ email, ...meta }) + '\n')
  : null;

/* ---------- server ---------- */

const [redirects, headerBlocks] = await Promise.all([loadRedirects(), loadHeaders()]);
console.log(`loaded ${redirects.length} redirect rules, ${headerBlocks.length} header blocks`);

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  let pathname = url.pathname;

  // Anything not served from the real domain (Railway preview hosts,
  // localhost) is a staging copy and must never be indexed — it would
  // compete with paititi-institute.org after launch.
  const host = (req.headers.host || '').replace(/:\d+$/, '');
  if (!/^(www\.)?paititi-institute\.org$/i.test(host)) {
    res.setHeader('X-Robots-Tag', 'noindex');
  }

  try {
    // 1. API
    if (pathname.startsWith('/api/')) {
      let body = null;
      if (req.method === 'POST') {
        const chunks = [];
        for await (const c of req) chunks.push(c);
        try { body = JSON.parse(Buffer.concat(chunks).toString('utf8')); } catch { body = null; }
      }
      const origin = process.env.SITE_ORIGIN || url.origin;
      const { status, body: payload } = await handleApi({
        method: req.method, pathname, body, env: process.env, origin,
        deps: {
          readCatalog: async () =>
            JSON.parse(await readFile(join(ROOT, 'data', 'products.json'), 'utf8')),
          saveSubscriber,
        },
      });
      return send(res, status, JSON_HEADERS, JSON.stringify(payload));
    }

    // 2. _redirects — 200 rewrites keep the URL, 30x tell the browser to move.
    // "/journal/* /blog/:splat"-style suffix wildcards match like Cloudflare's.
    for (const rule of redirects) {
      let to = null;
      if (rule.from === pathname) {
        to = rule.to;
      } else if (rule.from.endsWith('/*')) {
        const base = rule.from.slice(0, -2);
        if (pathname.startsWith(base + '/') && pathname.length > base.length + 1) {
          to = rule.to.replace(':splat', pathname.slice(base.length + 1));
        }
      }
      if (to === null) continue;
      if (rule.status === 200) { pathname = to; break; }
      if (/^https?:\/\//.test(to) || rule.status >= 300) {
        return send(res, rule.status, { location: to }, '');
      }
    }

    // 3. static file
    const file = await resolveFile(pathname);
    if (!file) {
      const notFound = await resolveFile('/404.html');
      if (notFound) {
        res.writeHead(404, { 'content-type': MIME['.html'] });
        return createReadStream(notFound.abs).pipe(res);
      }
      return send(res, 404, { 'content-type': 'text/plain; charset=utf-8' }, 'Not found');
    }

    const type = MIME[extname(file.abs).toLowerCase()] || 'application/octet-stream';
    const extra = headersFor(pathname, headerBlocks);
    // Hashed-by-content these are not, so let assets revalidate rather than
    // pinning a long max-age that would strand an updated image.
    if (!extra['Cache-Control']) {
      extra['Cache-Control'] = pathname.startsWith('/assets/')
        ? 'public, max-age=3600'
        : 'public, max-age=0, must-revalidate';
    }
    res.writeHead(200, { 'content-type': type, 'content-length': file.size, ...extra });
    if (req.method === 'HEAD') return res.end();
    createReadStream(file.abs).pipe(res);
  } catch (e) {
    console.error('server error', pathname, e);
    send(res, 500, { 'content-type': 'text/plain; charset=utf-8' }, 'Internal error');
  }
});

server.listen(PORT, () => console.log(`Paititi site listening on :${PORT}`));
