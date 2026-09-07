#!/usr/bin/env node
/**
 * Does the site side of Google Tag Assistant's connection work?
 *
 *   node tools/tag_assistant_probe.mjs [https://paititi-institute.org/retreats]
 *
 * Tag Assistant (tagassistant.google.com — also what "Troubleshoot" on a
 * conversion action in Google Ads opens) connects like this: it opens the page
 * in a named popup with ?gtm_debug=<timestamp>; gtag.js sees that parameter
 * and pulls a debug bootstrap from googletagmanager.com; the bootstrap listens
 * for `PING` messages from the opener and, only if they come from the origin
 * https://tagassistant.google.com, answers each one and reports every tag on
 * the page as `CONTAINER_STARTING`. It gives up if the first ping has not
 * arrived within five seconds of DOMContentLoaded. The page never contacts
 * tagassistant.google.com itself; everything is window-to-window postMessage.
 *
 * So "Tag Assistant couldn't connect" has two very different causes — the
 * site (a CSP that refuses googletagmanager.com, a Cross-Origin-Opener-Policy
 * that severs the popup from its opener, a redirect that drops the parameter,
 * a script that navigates away) and the tester's browser (an ad blocker,
 * Ghostery, Privacy Badger, Firefox's strict tracking protection, all of which
 * drop googletagmanager.com so the tag never loads there while it keeps
 * counting everyone else). Nothing in the Tag Assistant UI says which.
 *
 * This script settles it. It plays Tag Assistant in a headless Chrome: a
 * local HTTPS server answers as https://tagassistant.google.com (Chrome is
 * sent through a local CONNECT proxy that tunnels that one host to the local
 * server and everything else to the real internet, and told to ignore the
 * self-signed certificate), opens the target in a popup exactly as Tag
 * Assistant does, pings it, and prints what came back. A CONTAINER_STARTING
 * for GT-MBL4BMP means the site side is fine and the problem is the browser
 * that ran the real test. It also lists every request the debug flow made and
 * anything the Content-Security-Policy refused — that is how the badge
 * stylesheet's style-src block was found on 7 Sep 2026.
 *
 * Needs Google Chrome (path in $CHROME, default /Applications) and openssl.
 * Does not touch the repo or the live site; leaves nothing behind but a
 * temp directory.
 */
import { spawn, execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import https from 'node:https';
import http from 'node:http';
import net from 'node:net';

const target = process.argv[2] || 'https://paititi-institute.org/retreats';
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const dir = mkdtempSync(join(tmpdir(), 'tag-assistant-probe-'));
const rnd = () => Math.floor(Math.random() * 100);
const cdpPort = 9800 + rnd(), tlsPort = 8443 + rnd(), proxyPort = 8600 + rnd();

// Self-signed certificate for the fake Tag Assistant origin.
execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', join(dir, 'ta.key'),
  '-out', join(dir, 'ta.crt'), '-days', '1', '-subj', '/CN=tagassistant.google.com',
  '-addext', 'subjectAltName=DNS:tagassistant.google.com'], { stdio: 'ignore' });

// The fake Tag Assistant page: open the popup the way the real one does, ping it, log replies.
const page = `<!doctype html><title>fake tag assistant</title><script>
window.__log = [];
var u = new URLSearchParams(location.search).get('u');
window.addEventListener('message', function (e) {
  var d; try { d = JSON.stringify(e.data); } catch (x) { d = String(e.data); }
  window.__log.push({ t: Date.now(), origin: e.origin, type: e.data && e.data.type, data: d.slice(0, 700) });
});
var url = u + (u.indexOf('?') >= 0 ? '&' : '?') + 'gtm_debug=' + Date.now();
window.__popup = window.open(url, 'tag-assistant-debug-window-probe');
window.__opened = !!window.__popup;
setInterval(function () {
  try { window.__popup && window.__popup.postMessage({ type: 'PING', locale: 'en' }, '*'); }
  catch (e) { window.__log.push({ err: String(e) }); }
}, 500);
</script>`;

const tls = https.createServer({ key: readFileSync(join(dir, 'ta.key')), cert: readFileSync(join(dir, 'ta.crt')) }, (req, res) => {
  res.writeHead(200, { 'content-type': 'text/html' }); res.end(page);
});
await new Promise((r, j) => tls.listen(tlsPort, '127.0.0.1', r).on('error', j));

// CONNECT proxy: tagassistant.google.com -> local TLS server, anything else -> the real host.
const proxy = http.createServer((req, res) => { res.writeHead(400); res.end(); });
proxy.on('connect', (req, clientSock, head) => {
  const [host, p] = req.url.split(':');
  const upstream = host === 'tagassistant.google.com' ? net.connect(tlsPort, '127.0.0.1') : net.connect(Number(p || 443), host);
  upstream.on('connect', () => {
    clientSock.write('HTTP/1.1 200 Connection Established\r\n\r\n');
    if (head?.length) upstream.write(head);
    upstream.pipe(clientSock); clientSock.pipe(upstream);
  });
  upstream.on('error', () => clientSock.destroy());
  clientSock.on('error', () => upstream.destroy());
});
await new Promise((r, j) => proxy.listen(proxyPort, '127.0.0.1', r).on('error', j));

const chrome = spawn(CHROME, [
  '--headless=new', `--remote-debugging-port=${cdpPort}`, `--user-data-dir=${join(dir, 'profile')}`,
  '--no-first-run', '--no-default-browser-check', '--disable-gpu', '--window-size=1440,900',
  `--proxy-server=http://127.0.0.1:${proxyPort}`, '--ignore-certificate-errors',
  '--disable-popup-blocking', 'about:blank',
], { stdio: ['ignore', 'ignore', 'ignore'] });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function version() {
  for (let i = 0; i < 50; i++) {
    try { return await (await fetch(`http://127.0.0.1:${cdpPort}/json/version`)).json(); } catch { await sleep(200); }
  }
  throw new Error(`Chrome did not start (${CHROME})`);
}
const { webSocketDebuggerUrl } = await version();
const ws = new WebSocket(webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map(); const listeners = [];
ws.onmessage = (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  else if (m.method) listeners.forEach((l) => l(m));
};
function send(method, params = {}, sessionId) {
  return new Promise((resolve) => { const mid = ++id; pending.set(mid, resolve); ws.send(JSON.stringify({ id: mid, method, params, sessionId })); });
}

// Attach to every page that appears, so the popup's console and network are visible too.
const sessions = new Map();
listeners.push(async (m) => {
  if (m.method === 'Target.attachedToTarget' && m.params.targetInfo.type === 'page') {
    const sid = m.params.sessionId;
    sessions.set(sid, { url: m.params.targetInfo.url, logs: [], failed: [], requests: [], exceptions: [] });
    await send('Network.enable', {}, sid); await send('Log.enable', {}, sid); await send('Runtime.enable', {}, sid); await send('Page.enable', {}, sid);
    await send('Emulation.setUserAgentOverride', { userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36' }, sid);
    if (m.params.waitingForDebugger) await send('Runtime.runIfWaitingForDebugger', {}, sid);
  }
  const s = sessions.get(m.sessionId); if (!s) return;
  if (m.method === 'Network.requestWillBeSent') s.requests.push({ id: m.params.requestId, url: m.params.request.url, type: m.params.type });
  if (m.method === 'Network.loadingFailed') s.failed.push({ id: m.params.requestId, err: m.params.errorText, blocked: m.params.blockedReason });
  if (m.method === 'Log.entryAdded') s.logs.push(`${m.params.entry.level} [${m.params.entry.source}] ${m.params.entry.text}`);
  if (m.method === 'Runtime.exceptionThrown') s.exceptions.push(m.params.exceptionDetails.exception?.description?.slice(0, 300) || m.params.exceptionDetails.text);
  if (m.method === 'Page.frameNavigated' && !m.params.frame.parentId) s.url = m.params.frame.url;
});
await send('Target.setAutoAttach', { autoAttach: true, waitForDebuggerOnStart: true, flatten: true });
await send('Target.createTarget', { url: 'about:blank' });
await sleep(800);
const taSid = [...sessions.keys()][0];
await send('Page.navigate', { url: `https://tagassistant.google.com/?u=${encodeURIComponent(target)}` }, taSid);
await sleep(15000);

const evalIn = async (sid, expression) => (await send('Runtime.evaluate', { expression, returnByValue: true }, sid)).result?.result?.value;
const ta = JSON.parse(await evalIn(taSid, 'JSON.stringify({ opened: window.__opened, log: window.__log })') || '{}');
const counts = {};
for (const e of ta.log || []) counts[e.type || e.err || '?'] = (counts[e.type || e.err || '?'] || 0) + 1;
const started = (ta.log || []).filter((x) => x.type === 'CONTAINER_STARTING');

console.log(`Target: ${target}`);
console.log(`Popup opened: ${ta.opened}`);
console.log(`Messages the page sent back to tagassistant.google.com, by type: ${JSON.stringify(counts)}`);
for (const e of started) {
  const d = JSON.parse(e.data).data || {};
  console.log(`  tag ${d.id} → destinations ${JSON.stringify(d.destinations)} from ${d.scriptSource}`);
}

for (const [sid, s] of sessions) {
  if (sid === taSid || !/^https?:/.test(s.url)) continue;
  console.log(`\nPopup: ${s.url}`);
  const st = await evalIn(sid, `JSON.stringify((function(){
    var f = Array.from(document.querySelectorAll('iframe')).find(function(x){ try { return x.contentWindow && x.contentWindow.debugBadgeApi; } catch (e) { return false; } });
    var api = f && f.contentWindow.debugBadgeApi;
    return { name: window.name, opener: !!window.opener, badge: api ? api.getState() : 'no badge' };
  })())`);
  console.log(`  window.name / opener / badge: ${st}`);
  for (const r of s.requests.filter((x) => /googletagmanager|tagassistant/.test(x.url))) {
    const f = s.failed.find((x) => x.id === r.id);
    console.log(`  ${f ? 'BLOCKED(' + (f.blocked || f.err) + ')' : 'ok'} ${r.type} ${r.url.slice(0, 120)}`);
  }
  const csp = s.logs.filter((l) => /Content Security Policy/.test(l));
  if (csp.length) console.log('  CSP refused:\n    ' + csp.join('\n    '));
  if (s.exceptions.length) console.log('  exceptions:\n    ' + s.exceptions.join('\n    '));
}

console.log('');
if (started.length) console.log('VERDICT: the site completes the Tag Assistant handshake. If the real Tag Assistant still cannot connect, the browser running it is blocking googletagmanager.com — try Chrome with extensions off (Incognito) or the Tag Assistant Companion extension.');
else if (!ta.opened) console.log('VERDICT: the popup could not be opened — this probe is broken, not the site.');
else console.log('VERDICT: the page never answered. The site side is at fault — look at the BLOCKED lines and CSP refusals above, and check the live headers for Cross-Origin-Opener-Policy or a redirect that drops ?gtm_debug.');

chrome.kill('SIGKILL'); tls.close(); proxy.close();
rmSync(dir, { recursive: true, force: true });
process.exit(started.length ? 0 : 1);
