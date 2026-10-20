"""Refresh the "Recent articles" list in README.md from the Substack feed.

Rewrites only the lines between <!-- SUBSTACK:START --> and <!-- SUBSTACK:END -->.
If the feed can't be read or has no posts, it exits with an error and leaves
the README untouched.

Usage: python3 scripts/substack.py [feed-file]   (a local file is for testing)
"""
from datetime import datetime
import email.utils
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

FEED = "https://mutawa.substack.com/feed"
ARCHIVE = "https://mutawa.substack.com/api/v1/archive?sort=new&limit=12"
RELAY = "https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fmutawa.substack.com%2Ffeed"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
      "Accept": "application/rss+xml, application/json, text/xml, */*"}
README = "README.md"
COUNT = 5
START, END = "<!-- SUBSTACK:START -->", "<!-- SUBSTACK:END -->"


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read()


def from_archive():
    """Fallback: Substack's JSON archive, used when the RSS feed is refused."""
    out = []
    for p in json.loads(get(ARCHIVE)):
        if p.get("type", "newsletter") != "newsletter" or not p.get("title"):
            continue
        date = datetime.fromisoformat(p["post_date"].replace("Z", "+00:00"))
        out.append((date, p["title"].strip(), p.get("canonical_url", "").split("?")[0]))
    out.sort(reverse=True)
    return out[:COUNT]


def from_relay():
    """Fallback: rss2json reads the same public feed when Substack blocks GitHub's servers."""
    data = json.loads(get(RELAY))
    if data.get("status") != "ok":
        raise RuntimeError(data.get("message", "relay error"))
    out = []
    for p in data.get("items", []):
        date = datetime.strptime(p["pubDate"], "%Y-%m-%d %H:%M:%S")
        out.append((date, p["title"].strip(), p["link"].split("?")[0]))
    out.sort(reverse=True)
    return out[:COUNT]


def fetch_posts(src):
    if src:
        return posts(open(src, "rb").read())
    errors = []
    try:
        return posts(get(FEED))
    except Exception as e:
        errors.append(f"RSS feed: {e}")
    try:
        return from_archive()
    except Exception as e:
        errors.append(f"JSON archive: {e}")
    try:
        return from_relay()
    except Exception as e:
        errors.append(f"rss2json: {e}")
    print("::error::Could not read Substack. " + " | ".join(errors))
    sys.exit(1)


def posts(xml):
    out = []
    for item in ET.fromstring(xml).iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip().split("?")[0]
        date = email.utils.parsedate_to_datetime(item.findtext("pubDate"))
        if title and link:
            out.append((date, title, link))
    out.sort(reverse=True)
    return out[:COUNT]


def md(title):
    return title.replace("[", "\\[").replace("]", "\\]")


def main():
    items = fetch_posts(sys.argv[1] if len(sys.argv) > 1 else None)
    if not items:
        sys.exit("No posts found in the feed; README left unchanged.")
    lines = "\n".join(f"- [{md(t)}]({l}) — {d.strftime('%b %Y')}" for d, t, l in items)
    text = open(README, encoding="utf-8").read()
    if START not in text or END not in text:
        sys.exit("Markers missing from README; nothing changed.")
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: f"{START}\n{lines}\n{END}", text, flags=re.S)
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
        print("README updated:\n" + lines)
    else:
        print("Already up to date.")


if __name__ == "__main__":
    main()
