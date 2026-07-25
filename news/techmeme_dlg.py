#!/usr/bin/env python3
"""
techmeme_dlg.py — surface Techmeme headlines that matter to DLG / LuxuryIQ.

What it does
------------
1. Pulls the Techmeme river (RSS feed by default, the /m/ mobile page as a
   fallback) or reads a local file you pass with --input.
2. Scores every headline against the DLG / LuxuryIQ relevance model in
   relevance_config.json (editable: themes, keywords, weights, thresholds).
3. Keeps only the items that clear the "medium" bar, ranks them, and for each
   one attaches WHY it matters to DLG and a concrete idea/suggestion to act on.
4. Prints a markdown brief (default) or JSON.

The scoring is deterministic and transparent — it decides *which* headlines are
worth your attention and gives a first-pass angle. The richer, headline-specific
analysis is meant to be layered on top by Claude (see the techmeme-dlg-brief
skill), which reads this tool's JSON output.

Stdlib only. No third-party dependencies.

Usage
-----
  python3 techmeme_dlg.py                      # live feed -> markdown brief
  python3 techmeme_dlg.py --format json        # live feed -> JSON (for Claude)
  python3 techmeme_dlg.py --input sample_feed.xml   # offline / testing
  python3 techmeme_dlg.py --min high           # only the top-bucket items
  python3 techmeme_dlg.py --limit 12

Note: some managed/web environments block techmeme.com at the network policy.
If a live fetch fails, run the tool where Techmeme is reachable, or feed it a
saved feed file with --input.
"""

import argparse
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

DEFAULT_FEED = "https://www.techmeme.com/feed.xml"
FALLBACK_PAGE = "https://www.techmeme.com/m/"
USER_AGENT = "Mozilla/5.0 (compatible; DLG-LuxuryIQ-news/1.0)"
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(HERE, "relevance_config.json")


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #
def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def load_source(url, input_path, page_fallback):
    """Return (text, kind) where kind is 'xml' or 'html'."""
    if input_path:
        with open(input_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        kind = "html" if "<item" not in text and "<rss" not in text else "xml"
        return text, kind

    try:
        return fetch(url), "xml"
    except Exception as feed_err:  # noqa: BLE001
        sys.stderr.write(
            "feed fetch failed (%s); trying %s\n" % (feed_err, page_fallback)
        )
        try:
            return fetch(page_fallback), "html"
        except Exception as page_err:  # noqa: BLE001
            raise SystemExit(
                "Could not reach Techmeme. Feed error: %s | Page error: %s\n"
                "This environment may block techmeme.com. Run where it is "
                "reachable, or pass a saved feed with --input." % (feed_err, page_err)
            )


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def _clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


ITEM_RE = re.compile(r"<item\b.*?>(.*?)</item>", re.DOTALL | re.IGNORECASE)
TAG_RE = {
    "title": re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE),
    "link": re.compile(r"<link>(.*?)</link>", re.DOTALL | re.IGNORECASE),
    "desc": re.compile(r"<description>(.*?)</description>", re.DOTALL | re.IGNORECASE),
    "date": re.compile(r"<pubDate>(.*?)</pubDate>", re.DOTALL | re.IGNORECASE),
}
# Techmeme headlines often read "Source Author / Outlet: Headline text".
SOURCE_RE = re.compile(r"^([^:]{2,60}):\s+(.*)$")


def _strip_cdata(text):
    return re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text or "", flags=re.DOTALL)


def parse_xml(text):
    items = []
    for block in ITEM_RE.findall(text):
        title_raw = _clean(_strip_cdata(_first(TAG_RE["title"], block)))
        if not title_raw:
            continue
        link = _clean(_strip_cdata(_first(TAG_RE["link"], block)))
        desc = _clean(_strip_cdata(_first(TAG_RE["desc"], block)))
        date = _clean(_first(TAG_RE["date"], block))
        headline, source = title_raw, ""
        m = SOURCE_RE.match(title_raw)
        if m:
            source, headline = m.group(1).strip(), m.group(2).strip()
        items.append(
            {
                "headline": headline,
                "source": source,
                "link": link,
                "summary": desc,
                "published": date,
            }
        )
    return items


LINK_RE = re.compile(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', re.DOTALL | re.IGNORECASE)


def parse_html(text):
    """Best-effort fallback: scrape anchor headlines off the /m/ page."""
    items, seen = [], set()
    for href, label in LINK_RE.findall(text):
        headline = _clean(label)
        if len(headline) < 25 or headline in seen:
            continue
        if "techmeme.com" in href:
            continue
        seen.add(headline)
        items.append(
            {"headline": headline, "source": "", "link": href, "summary": "", "published": ""}
        )
    return items


def _first(regex, text):
    m = regex.search(text)
    return m.group(1) if m else ""


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def load_config(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _matches(keyword, haystack):
    kw = keyword.lower()
    # Multi-word or symbol-padded keywords: plain substring.
    if " " in kw or not kw.strip().isalnum():
        return kw in haystack
    # Single word: token-boundary match to avoid false hits inside longer words.
    return re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(kw), haystack) is not None


def score_item(item, config):
    hay = (" " + item["headline"] + " " + item["source"] + " " + item["summary"] + " ").lower()
    score = 0
    themes = []
    for theme in config["themes"]:
        hits = [k for k in theme["keywords"] if _matches(k, hay)]
        if hits:
            score += theme["weight"]
            themes.append(
                {
                    "id": theme["id"],
                    "label": theme["label"],
                    "weight": theme["weight"],
                    "matched": hits,
                    "dlg_angle": theme.get("dlg_angle", ""),
                    "idea": theme.get("idea", ""),
                }
            )
    if any(_matches(n, hay) for n in config.get("noise_keywords", [])):
        score -= 2
    item["score"] = score
    item["themes"] = themes
    return item


def bucket(score, thresholds):
    if score >= thresholds["high"]:
        return "high"
    if score >= thresholds["medium"]:
        return "medium"
    return "drop"


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def build(items, config, min_bucket, limit):
    order = {"high": 2, "medium": 1, "drop": 0}
    scored = [score_item(dict(it), config) for it in items]
    for it in scored:
        it["bucket"] = bucket(it["score"], config["thresholds"])
    kept = [it for it in scored if order[it["bucket"]] >= order[min_bucket]]
    kept.sort(key=lambda it: (it["score"], it["bucket"] == "high"), reverse=True)
    if limit:
        kept = kept[:limit]
    return kept, len(scored)


def render_markdown(kept, total_seen, generated_at):
    lines = []
    lines.append("# Techmeme brief for DLG / LuxuryIQ")
    lines.append("")
    lines.append(
        "_%s — %d relevant of %d headlines scanned. Analysis shown only where a "
        "headline clears the relevance bar._" % (generated_at, len(kept), total_seen)
    )
    lines.append("")
    if not kept:
        lines.append("Nothing on the river cleared the relevance bar this run.")
        return "\n".join(lines)

    highs = [it for it in kept if it["bucket"] == "high"]
    meds = [it for it in kept if it["bucket"] == "medium"]

    def block(it):
        out = []
        title = it["headline"]
        if it["link"]:
            title = "[%s](%s)" % (it["headline"], it["link"])
        src = (" — %s" % it["source"]) if it["source"] else ""
        out.append("### %s%s" % (title, src))
        labels = ", ".join(t["label"] for t in it["themes"])
        out.append("`score %d` · %s" % (it["score"], labels))
        # De-duplicate angle/idea across matched themes, keep order.
        angles, ideas, seen_a, seen_i = [], [], set(), set()
        for t in it["themes"]:
            a, i = t["dlg_angle"], t["idea"]
            if a and a not in seen_a:
                angles.append(a); seen_a.add(a)
            if i and i not in seen_i:
                ideas.append(i); seen_i.add(i)
        if angles:
            out.append("")
            out.append("**Why it matters:** " + " ".join(angles))
        if ideas:
            out.append("")
            out.append("**Idea / suggestion:** " + " ".join(ideas))
        out.append("")
        return "\n".join(out)

    if highs:
        lines.append("## High relevance")
        lines.append("")
        lines.extend(block(it) for it in highs)
    if meds:
        lines.append("## Worth a look")
        lines.append("")
        lines.extend(block(it) for it in meds)
    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None):
    p = argparse.ArgumentParser(description="Surface DLG/LuxuryIQ-relevant Techmeme news.")
    p.add_argument("--url", default=DEFAULT_FEED, help="Techmeme feed URL")
    p.add_argument("--page-fallback", default=FALLBACK_PAGE, help="HTML page fallback URL")
    p.add_argument("--input", help="Read a local feed/page file instead of fetching")
    p.add_argument("--config", default=DEFAULT_CONFIG, help="Relevance config JSON")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--min", choices=["high", "medium"], default="medium", help="Lowest bucket to keep")
    p.add_argument("--limit", type=int, default=0, help="Cap number of items (0 = no cap)")
    args = p.parse_args(argv)

    config = load_config(args.config)
    text, kind = load_source(args.url, args.input, args.page_fallback)
    items = parse_xml(text) if kind == "xml" else parse_html(text)
    if not items:
        raise SystemExit("Parsed 0 headlines. The feed format may have changed.")

    kept, total = build(items, config, args.min, args.limit)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if args.format == "json":
        print(json.dumps(
            {"generated_at": generated_at, "scanned": total, "kept": kept},
            indent=2, ensure_ascii=False,
        ))
    else:
        print(render_markdown(kept, total, generated_at))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
