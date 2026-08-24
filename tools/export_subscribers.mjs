#!/usr/bin/env node
/**
 * Export newsletter sign-ups collected by the site into a CSV that Squarespace
 * (or any provider) will import.
 *
 *   node tools/export_subscribers.mjs                 # → subscribers-YYYY-MM-DD.csv
 *   node tools/export_subscribers.mjs --since 2026-09-01
 *   node tools/export_subscribers.mjs --out /tmp/list.csv
 *
 * Until a newsletter provider is wired up, /api/newsletter puts each address
 * into the Cloudflare KV namespace bound as NEWSLETTER (see api.js). This reads
 * that namespace through wrangler and writes the three columns Squarespace
 * wants, in the order it wants them: email, first name, last name.
 *
 * Squarespace: Lists & Segments → the list → Add Subscribers → Upload a list →
 * tick "These subscribers accept marketing" → Import.
 *
 * Requires: wrangler logged in (`npx wrangler login`) and a `kv_namespaces`
 * entry for NEWSLETTER in wrangler.jsonc.
 */

import { execFileSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';

const args = process.argv.slice(2);
const flag = (name) => {
  const i = args.indexOf(name);
  return i === -1 ? null : args[i + 1];
};

const since = flag('--since');
const today = new Date().toISOString().slice(0, 10);
const out = flag('--out') || `subscribers-${today}.csv`;

if (since && Number.isNaN(Date.parse(since))) {
  console.error(`--since expects a date like 2026-09-01, got "${since}"`);
  process.exit(1);
}

const wrangler = (...argv) => {
  try {
    return execFileSync('npx', ['--yes', 'wrangler', ...argv], {
      encoding: 'utf8',
      maxBuffer: 64 * 1024 * 1024,
      stdio: ['ignore', 'pipe', 'inherit'],
    });
  } catch (e) {
    console.error(
      '\nwrangler failed. Check that you are logged in (`npx wrangler login`)\n' +
      'and that wrangler.jsonc has a kv_namespaces entry binding NEWSLETTER.\n'
    );
    process.exit(1);
  }
};

console.error('Reading the NEWSLETTER namespace…');
const keys = JSON.parse(wrangler('kv', 'key', 'list', '--binding', 'NEWSLETTER', '--remote'));

if (keys.length === 0) {
  console.error('No sign-ups stored yet — nothing to export.');
  process.exit(0);
}

const rows = [];
let skipped = 0;

for (const [i, { name: email }] of keys.entries()) {
  process.stderr.write(`\r${i + 1}/${keys.length}`);

  let meta = {};
  if (since) {
    // Only the stored value carries the timestamp, so a date filter costs one
    // read per address. Without --since we never fetch the values at all.
    const raw = wrangler('kv', 'key', 'get', email, '--binding', 'NEWSLETTER', '--remote');
    try { meta = JSON.parse(raw); } catch { /* older entries may be bare */ }
    if (meta.ts && Date.parse(meta.ts) < Date.parse(since)) { skipped++; continue; }
  }
  rows.push(email);
}
process.stderr.write('\n');

// Squarespace wants exactly three columns in this order; we only ever collected
// the address, so the name columns stay empty rather than being invented.
const csv = ['Email Address,First Name,Last Name']
  .concat(rows.map((e) => `${e.includes(',') ? `"${e}"` : e},,`))
  .join('\n');

writeFileSync(out, `${csv}\n`);
console.error(
  `Wrote ${rows.length} address${rows.length === 1 ? '' : 'es'} to ${out}` +
  (skipped ? ` (${skipped} older than ${since} skipped)` : '')
);
