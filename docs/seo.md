# SEO setup — template

The skeleton ships with `noindex` on every page and `example.com` as the
domain placeholder. Before launch:

1. **Domain** — find-and-replace `example.com` across the repo (canonical URLs,
   OG tags, `robots.txt`, `sitemap.xml`).
2. **Unblock indexing** — remove `<meta name="robots" content="noindex">` from
   pages that should rank; keep it on utility pages (demos, fragments).
   `SiteHeader.dc.html`/`SiteFooter.dc.html` stay noindexed via `_headers`.
3. **Per-page meta** — unique `<title>` (~55 chars) and `<meta name="description">`
   (~155 chars) in each page's `<helmet>`; OG + Twitter tags; a real
   `og-image.png` (1200×630) in `assets/`.
4. **Structured data** — add an `Organization` + `WebSite` JSON-LD block to the
   home page.
5. **Sitemap** — one `<url>` per public page; submit in Search Console.
6. **Clean URLs** — `_redirects` covers Netlify/Cloudflare. Other hosts:
   - **Vercel**: `rewrites` in `vercel.json`
   - **Nginx/Apache**: `try_files` / `RewriteRule` (see `nginx.conf.template`)
   - **GitHub Pages**: files serve at their real names; keep `.nojekyll`
     (without it, Pages' Jekyll step silently drops the `_ds/` folder).
