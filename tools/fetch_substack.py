#!/usr/bin/env python3
"""Mirror the Substack RSS feed into the _substack collection.

Each post becomes a small Jekyll document in _substack/, so it shows up in the
articles list on /blog/ exactly like a normal post — same markup, sorted by
date alongside the vignettes. The collection has output: false, so no thin
duplicate pages are generated; each entry links straight to Substack.

Runs daily from .github/workflows/substack.yml, or by hand:
    python3 tools/fetch_substack.py

Design notes:
  * Standard library only — no pip install, works on any runner.
  * Fetched at BUILD time, not in the browser: Substack sends no CORS header,
    so client-side fetch() is blocked. Build-time also means no third-party
    proxy and no extra requests for visitors.
  * Entries are only added/updated, never deleted: the feed holds just the
    most recent posts, so pruning would make older ones vanish over time.
  * On network/parse failure nothing is written and the script exits non-zero,
    so the site keeps every post it already has while the run shows up red.
"""

import email.utils
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timezone

FEED_URL = os.environ.get("SUBSTACK_FEED", "https://marimana.substack.com/feed")
MAX_POSTS = int(os.environ.get("SUBSTACK_MAX_POSTS", "20"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "_substack")

NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}
# Substack rejects requests advertising themselves as Python (403), so send an
# ordinary browser UA — this is a public RSS feed being read the way any feed
# reader reads it. Override with SUBSTACK_UA if it ever needs adjusting.
UA = os.environ.get("SUBSTACK_UA", (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"))


def fetch(url, attempts=4):
    """GET url with retries and exponential backoff. Returns bytes."""
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5",
                "Accept-Language": "en-GB,en;q=0.9",
                "Cache-Control": "no-cache",
            })
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            last = e
            if i < attempts - 1:
                time.sleep(2 ** (i + 1))   # 2s, 4s, 8s
    raise RuntimeError(f"could not fetch {url}: {last}")


def text_of(node, path, default=""):
    el = node.find(path, NS)
    if el is None or el.text is None:
        return default
    return el.text.strip()


def strip_html(s, limit=320):
    """Turn an HTML fragment into a plain-text summary."""
    s = re.sub(r"(?is)<(script|style|form|svg)\b.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    s = " ".join(s.split())
    if len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0].rstrip(",.;:—-") + "…"
    return s


def slugify(url, title):
    """Stable file slug — prefer Substack's own /p/<slug>."""
    m = re.search(r"/p/([^/?#]+)", url)
    base = m.group(1) if m else title
    base = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    return base[:80] or "post"


def yaml_str(s):
    """Quote a value safely for YAML front matter."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def parse(xml_bytes):
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("no <channel> in feed — not an RSS document?")

    posts = []
    for item in channel.findall("item")[:MAX_POSTS]:
        title = html.unescape(text_of(item, "title"))
        link = text_of(item, "link")
        if not title or not link:
            continue

        summary = strip_html(text_of(item, "description"))
        if not summary:
            summary = strip_html(text_of(item, "content:encoded"))

        raw_date = text_of(item, "pubDate")
        try:
            dt = email.utils.parsedate_to_datetime(raw_date)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt = dt.astimezone(timezone.utc)
        except (TypeError, ValueError):
            continue                      # no usable date -> can't order it

        image = ""
        enc = item.find("enclosure")
        if enc is not None and enc.get("type", "").startswith("image"):
            image = enc.get("url", "")

        posts.append({
            "title": title,
            "url": link,
            "dt": dt,
            "summary": summary,
            "image": image,
        })
    return posts


def document(p):
    """Render one collection document."""
    lines = [
        "---",
        f"title: {yaml_str(p['title'])}",
        f"date: {p['dt'].strftime('%Y-%m-%d %H:%M:%S +0000')}",
        f"external_url: {yaml_str(p['url'])}",
        "source: Substack",
    ]
    if p["summary"]:
        lines.append(f"summary: {yaml_str(p['summary'])}")
    if p["image"]:
        lines.append(f"image: {yaml_str(p['image'])}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def main():
    try:
        posts = parse(fetch(FEED_URL))
    except Exception as e:                                  # noqa: BLE001
        print(f"Substack fetch failed: {e}", file=sys.stderr)
        print("Nothing written; existing entries left in place.", file=sys.stderr)
        # Substack blocks datacenter IPs, so scheduled CI runs get a 403 even
        # with a browser UA, while the same request succeeds from a normal
        # connection. Report that as "blocked" (exit 2) rather than a hard
        # failure, so a daily job can skip quietly instead of paging you.
        if "403" in str(e) or "Forbidden" in str(e):
            return 2
        return 1

    if not posts:
        print("::error::feed parsed but contained no usable posts", file=sys.stderr)
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    added = updated = 0

    for p in posts:
        path = os.path.join(OUT_DIR, f"{p['dt'].strftime('%Y-%m-%d')}-{slugify(p['url'], p['title'])}.md")
        body = document(p)
        old = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                old = f.read()
        if old == body:
            continue
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, path)                                # atomic
        if old is None:
            added += 1
            print(f"  + {os.path.basename(path)}")
        else:
            updated += 1
            print(f"  ~ {os.path.basename(path)}")

    total = len([f for f in os.listdir(OUT_DIR) if f.endswith(".md")])
    if added or updated:
        print(f"Substack: {added} added, {updated} updated ({total} total).")
    else:
        print(f"Substack: no change ({total} post(s) already current).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
