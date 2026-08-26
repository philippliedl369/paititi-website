#!/usr/bin/env python3
"""Recover the blog's source data out of the generated English pages.

Why this exists: tools/migrate_blog.py was written as a one-time Squarespace
migration and reads its source from `paititi-institute.org/blog?format=json`.
Since the Cloudflare migration on 25 Aug 2026 that URL serves the static
Blog.dc.html instead, so the generator can no longer fetch anything and the
README's "edit the generator and re-run it" rule cannot actually be followed.

The posts themselves survive, in the pages the generator already wrote. This
lifts them back out into data/blog/posts.json, which migrate_blog.py then reads
instead of the network. Two things fall out of that: the generator becomes
re-runnable again, and it gains a source it can render into more than one
language.

    python3 tools/blog_snapshot.py            # write data/blog/posts.json
    python3 tools/blog_snapshot.py --check    # compare against the file, don't write

Run this only while the committed English pages are known-good — it treats them
as the source of truth, so anything wrong in them is what gets snapshotted.
"""
import glob
import html as htmllib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "blog", "posts.json")


def grab(pattern, text, what, path, default=None):
    m = re.search(pattern, text, re.S)
    if not m:
        if default is not None:
            return default
        raise SystemExit(f"{os.path.basename(path)}: could not find {what}")
    return m.group(1)


def read_post(path):
    s = open(path, encoding="utf-8").read()
    slug = os.path.basename(path)[len("BlogPost-"):-len(".dc.html")]

    title = grab(r"<title>(.*?) \| Paititi Institute</title>", s, "title", path)
    desc = grab(r'<meta name="description" content="(.*?)">', s, "description", path)
    iso = grab(r'<meta property="article:published_time" content="(.*?)">', s, "date", path)

    meta = grab(r'<p class="bp-meta">(.*?)</p>', s, "byline", path)
    cats = re.findall(r'<a href="/blog/category/([^"]+)">([^<]*)</a>', meta)
    author = grab(r'<a class="bp-author"[^>]*>(.*?)</a>', meta, "author", path)
    date = grab(r"<time datetime=\"[^\"]*\">(.*?)</time>", meta, "display date", path)

    # The body is everything between the wrapper div and the tag that closes it.
    # Squarespace's own markup is nested deeply and includes </div> at the same
    # six-space indent, so the terminator has to be the wrapper's closing tag
    # *followed by* </article> — matching on the indent alone truncated the
    # longest post at its first nested close.
    body = grab(r'<div class="bp-body pt-prose">\n(.*?)\n      </div>\n    </article>',
                s, "body", path)

    return {
        "slug": slug,
        "title": htmllib.unescape(title),
        # Stored escaped exactly as the page carries it: the generator writes it
        # straight into an attribute.
        "description": desc,
        "date": date,
        "iso_date": iso,
        "author": author,
        "categories": [{"slug": c, "name": htmllib.unescape(n)} for c, n in cats],
        "body": body,
    }


def read_index():
    """Card order, thumbnails and excerpts live on the index, not the posts."""
    path = os.path.join(ROOT, "Blog.dc.html")
    s = open(path, encoding="utf-8").read()
    cards = []
    for m in re.finditer(r'<article class="bl-card">(.*?)</article>', s, re.S):
        c = m.group(1)
        href = grab(r'<a class="bl-image" href="([^"]*)"', c, "card href", path)
        thumb = grab(r'<img src="/([^"]*)"', c, "card thumb", path)
        excerpt = grab(r'<div class="bl-excerpt">(.*?)</div>', c, "excerpt", path, default="")
        external = "sourceUrl" if href.startswith("http") else None
        cards.append({
            "href": href,
            "slug": href.rsplit("/", 1)[-1] if not external else None,
            "source_url": href if external else None,
            "thumb": thumb,
            "excerpt": excerpt.strip(),
            "title": htmllib.unescape(grab(r'<h2 class="bl-title"><a[^>]*>(.*?)</a>', c, "card title", path)),
            "author": grab(r"<p class=\"bl-meta\"><span>(.*?)</span>", c, "card author", path),
            "date": grab(r"<time datetime=\"([^\"]*)\">", c, "card iso", path),
            "date_display": grab(r"<time datetime=\"[^\"]*\">(.*?)</time>", c, "card date", path),
        })
    return cards


def main():
    check = "--check" in sys.argv
    posts = [read_post(p) for p in sorted(glob.glob(os.path.join(ROOT, "BlogPost-*.dc.html")))
             if ".es.dc.html" not in p]
    if not posts:
        raise SystemExit("no BlogPost-*.dc.html found")

    snapshot = {
        "_comment": [
            "Recovered from the generated English pages by tools/blog_snapshot.py.",
            "This is the blog's source of truth now that the Squarespace feed is gone.",
            "tools/migrate_blog.py renders it into both the English and Spanish trees.",
            "Spanish copy lives alongside it in data/blog/es.json, keyed by slug.",
        ],
        "cards": read_index(),
        "posts": posts,
    }
    text = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"

    if check:
        if not os.path.exists(OUT):
            print("no snapshot on disk yet")
            return 1
        same = open(OUT, encoding="utf-8").read() == text
        print("snapshot matches the pages" if same else "SNAPSHOT DIFFERS from the pages")
        return 0 if same else 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    words = sum(len(re.sub(r"(?s)<[^>]+>", " ", p["body"]).split()) for p in posts)
    print(f"wrote {os.path.relpath(OUT, ROOT)}")
    print(f"  {len(posts)} posts, {len(snapshot['cards'])} index cards, ~{words:,} words of body")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
