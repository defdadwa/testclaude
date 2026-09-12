#!/usr/bin/env python3
"""Human-in-the-loop capture of Geneva "publications foncieres" results.

This tool does NOT bypass the site's captcha or any other access control.
A real person opens the browser, clears the captcha and runs the search by
hand; the script only transcribes the results that are already on screen
into CSV, and tells you what is new since the previous run.

Usage:
    python3 capture.py                     # open browser, capture after search
    python3 capture.py --from-html f.html  # re-parse a saved capture
    python3 capture.py --list              # show past captures
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_URL = "https://publications-foncieres.app.ge.ch"
# Commune of Corsier GE. Matching on the name alone is deliberate: the postal
# code 1246 also turns up as a parcel number in other communes, so adding it
# to the default would pull in neighbours. Widen it by hand if you want it:
#   --filter 'corsier|\b1246\b'
DEFAULT_FILTER = r"corsier"

# Some machines already have a Chromium that Playwright can drive, and some
# sandboxes ship one at a fixed path. Point PF_CHROMIUM at it to skip the
# download that "playwright install" would otherwise do.
BROWSER_PATH_ENV = "PF_CHROMIUM"

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
CAPTURES_DIR = DATA_DIR / "captures"
SEEN_FILE = DATA_DIR / "seen.json"

# Extraction runs inside the page so it works on the live DOM and on a saved
# file alike. It is deliberately generic: tables first, then repeated blocks,
# then plain text lines. Once we have seen the real markup this can be
# replaced by a precise selector.
EXTRACT_JS = r"""
() => {
  const clean = (s) => (s || "").replace(/\s+/g, " ").trim();
  const rows = [];

  // 1. Real tables.
  document.querySelectorAll("table").forEach((table, ti) => {
    const headers = [...table.querySelectorAll("thead th, tr:first-child th")]
      .map((th) => clean(th.innerText));
    const trs = [...table.querySelectorAll("tbody tr")];
    const body = trs.length ? trs : [...table.querySelectorAll("tr")].slice(headers.length ? 1 : 0);
    body.forEach((tr) => {
      const cells = [...tr.querySelectorAll("td, th")].map((td) => clean(td.innerText));
      if (cells.some((c) => c)) {
        rows.push({ kind: "table", group: String(ti), headers, cells, text: cells.join(" | ") });
      }
    });
  });
  if (rows.length) return rows;

  // 2. Repeated sibling blocks (card / list layouts).
  const signature = (el) => el.tagName + "." + [...el.classList].sort().join(".");
  const candidates = [];
  document.querySelectorAll("body *").forEach((parent) => {
    const kids = [...parent.children];
    if (kids.length < 3) return;
    const sigs = new Set(kids.map(signature));
    if (sigs.size !== 1) return;
    const texts = kids.map((k) => clean(k.innerText)).filter((t) => t.length > 20);
    if (texts.length >= 3) candidates.push({ parent, texts });
  });
  if (candidates.length) {
    // Deepest repeated group wins: it is the row list, not the page shell.
    candidates.sort((a, b) => {
      const depth = (el) => { let d = 0; while (el.parentElement) { d++; el = el.parentElement; } return d; };
      return depth(b.parent) - depth(a.parent);
    });
    const best = candidates[0];
    best.texts.forEach((t, i) => {
      rows.push({ kind: "block", group: String(i), headers: [], cells: [t], text: t });
    });
    return rows;
  }

  // 3. Last resort: visible text lines.
  const main = document.querySelector("main") || document.body;
  clean(main.innerText).split(/\n+/).forEach((line, i) => {
    const t = clean(line);
    if (t.length > 20) rows.push({ kind: "line", group: String(i), headers: [], cells: [t], text: t });
  });
  return rows;
}
"""


def browser_kwargs(browser_path: str | None) -> dict:
    path = browser_path or os.environ.get(BROWSER_PATH_ENV)
    return {"executable_path": path} if path else {}


def row_key(text: str) -> str:
    """Stable identity for a result row, used to tell old from new."""
    normalised = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha1(normalised.encode("utf-8")).hexdigest()


def load_seen() -> dict:
    if SEEN_FILE.exists():
        return json.loads(SEEN_FILE.read_text(encoding="utf-8"))
    return {}


def save_seen(seen: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8")


def filter_rows(rows: list[dict], pattern: str) -> list[dict]:
    rx = re.compile(pattern, re.IGNORECASE)
    return [r for r in rows if rx.search(r.get("text", ""))]


def write_csv(rows: list[dict], path: Path, captured_at: str) -> None:
    width = max((len(r.get("cells") or []) for r in rows), default=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow(["capture", "type", "groupe", "texte"] + [f"col{i+1}" for i in range(width)])
        for r in rows:
            cells = list(r.get("cells") or [])
            cells += [""] * (width - len(cells))
            writer.writerow([captured_at, r.get("kind", ""), r.get("group", ""), r.get("text", "")] + cells)


def extract_from_page(page) -> list[dict]:
    return page.evaluate(EXTRACT_JS)


def capture_live(url: str, profile_dir: Path, browser_path: str | None) -> tuple[list[dict], str, str]:
    """Open a visible browser, wait for the human, then read the results."""
    from playwright.sync_api import sync_playwright

    profile_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,  # a person must see and use this window
            locale="fr-CH",
            viewport={"width": 1400, "height": 950},
            **browser_kwargs(browser_path),
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(url, wait_until="domcontentloaded")

        print()
        print("  Le navigateur est ouvert.")
        print("  1. Passe le captcha toi-même.")
        print("  2. Lance la recherche pour Corsier.")
        print("  3. Laisse les résultats affichés à l'écran.")
        print("  4. Reviens ici et appuie sur Entrée.")
        print()

        # Result lists are usually paginated, and only the person driving the
        # browser knows how many pages there are. So: capture, ask, repeat.
        rows: list[dict] = []
        pages_html: list[str] = []
        page_no = 1
        while True:
            input(f"  Entrée quand la page {page_no} des résultats est affichée > ")
            pages_html.append(page.content())
            rows.extend(extract_from_page(page))
            print(f"    page {page_no}: {len(rows)} ligne(s) lues au total")
            answer = input("  Une autre page de résultats à capturer ? [o/N] > ").strip().lower()
            if answer not in ("o", "oui", "y", "yes"):
                break
            page_no += 1

        context.close()
    separator = "\n<!-- ===== page suivante ===== -->\n"
    return rows, separator.join(pages_html), url


def capture_from_file(path: Path, browser_path: str | None) -> tuple[list[dict], str, str]:
    from playwright.sync_api import sync_playwright

    html = path.read_text(encoding="utf-8", errors="replace")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, **browser_kwargs(browser_path))
        page = browser.new_page()
        page.goto(path.resolve().as_uri(), wait_until="domcontentloaded")
        rows = extract_from_page(page)
        browser.close()
    return rows, html, str(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture des publications foncieres (Corsier 1246).")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--from-html", type=Path, help="re-parse a previously saved capture")
    parser.add_argument("--filter", default=DEFAULT_FILTER, help="regex kept, case-insensitive")
    parser.add_argument("--no-filter", action="store_true", help="keep every row, not only Corsier")
    parser.add_argument("--profile-dir", type=Path, default=DATA_DIR / "browser-profile")
    parser.add_argument("--browser-path", help=f"Chromium executable to use (or ${BROWSER_PATH_ENV})")
    parser.add_argument("--list", action="store_true", help="list past captures")
    args = parser.parse_args()

    if args.list:
        if not CAPTURES_DIR.exists():
            print("Aucune capture pour l'instant.")
            return 0
        for f in sorted(CAPTURES_DIR.glob("*.html")):
            print(f"  {f.name}  ({f.stat().st_size // 1024} Ko)")
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")

    if args.from_html:
        if not args.from_html.exists():
            print(f"Fichier introuvable: {args.from_html}", file=sys.stderr)
            return 1
        rows, html, origin = capture_from_file(args.from_html, args.browser_path)
    else:
        rows, html, origin = capture_live(args.url, args.profile_dir, args.browser_path)

    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    html_path = CAPTURES_DIR / f"{stamp}.html"
    html_path.write_text(html, encoding="utf-8")

    total = len(rows)
    unique: list[dict] = []
    seen_in_capture: set[str] = set()
    for r in rows:
        key = row_key(r.get("text", ""))
        if key not in seen_in_capture:
            seen_in_capture.add(key)
            unique.append(r)

    kept = unique if args.no_filter else filter_rows(unique, args.filter)

    csv_path = CAPTURES_DIR / f"{stamp}.csv"
    write_csv(kept, csv_path, stamp)

    seen = load_seen()
    fresh = [r for r in kept if row_key(r["text"]) not in seen]
    for r in kept:
        seen.setdefault(row_key(r["text"]), {"first_seen": stamp, "text": r["text"]})
    save_seen(seen)

    print()
    print(f"  Source            : {origin}")
    print(f"  Lignes lues       : {total} ({len(unique)} distinctes)")
    print(f"  Retenues          : {len(kept)}")
    print(f"  Nouvelles         : {len(fresh)}")
    print(f"  HTML archive      : {html_path}")
    print(f"  CSV               : {csv_path}")

    if fresh:
        new_path = CAPTURES_DIR / f"{stamp}-nouveautes.csv"
        write_csv(fresh, new_path, stamp)
        print(f"  Nouveautes        : {new_path}")
        print()
        for r in fresh[:20]:
            print(f"    + {r['text'][:160]}")
        if len(fresh) > 20:
            print(f"    ... et {len(fresh) - 20} de plus")

    if total and not kept and not args.no_filter:
        print()
        print(f"  Aucune ligne ne correspond au filtre: {args.filter}")
        print("  Relance avec --no-filter pour voir ce qui a été lu.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
