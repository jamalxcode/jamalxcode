"""Refresh the "Recent articles" list in README.md from the Substack feed.

Rewrites only the lines between <!-- SUBSTACK:START --> and <!-- SUBSTACK:END -->.
If the feed can't be read or has no posts, it exits with an error and leaves
the README untouched.

Usage: python3 scripts/substack.py [feed-file]   (a local file is for testing)
"""
import email.utils
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

FEED = "https://mutawa.substack.com/feed"
README = "README.md"
COUNT = 5
START, END = "<!-- SUBSTACK:START -->", "<!-- SUBSTACK:END -->"


def read_feed(src):
    if src:
        return open(src, "rb").read()
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0 (profile README updater)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


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
    items = posts(read_feed(sys.argv[1] if len(sys.argv) > 1 else None))
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
