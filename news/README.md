# Techmeme brief for DLG / LuxuryIQ

A small, dependency-free tool that reads the [Techmeme](https://www.techmeme.com/m/)
river and surfaces only the headlines that matter to Digital Luxury Group and
LuxuryIQ, with a short "why it matters" and one concrete idea for each item that
clears the relevance bar. Everything below the bar is dropped, so the output
stays short.

## What is here

| File | Purpose |
| --- | --- |
| `techmeme_dlg.py` | Fetch, score, and render the brief. Python 3 stdlib only. |
| `relevance_config.json` | The DLG / LuxuryIQ relevance model: themes, keywords, weights, thresholds, per-theme angle and idea seeds, noise list. Edit this to tune. |
| `sample_feed.xml` | A clearly-labelled fabricated fixture for testing offline. Not live data. |

There is also a Claude skill at `.claude/skills/techmeme-dlg-brief/` that runs
this tool and layers headline-specific analysis on top.

## Usage

```bash
# Live feed -> markdown brief
python3 techmeme_dlg.py

# Machine-readable output (this is what the Claude skill consumes)
python3 techmeme_dlg.py --format json

# Only the top bucket, capped at 10 items
python3 techmeme_dlg.py --min high --limit 10

# Offline / testing against the bundled sample
python3 techmeme_dlg.py --input sample_feed.xml
```

## How relevance is scored

The scorer is deterministic and transparent. Each headline (plus its source and
summary) is matched against the themes in `relevance_config.json`. A theme's
`weight` is added to the item's score for each theme it matches; a small penalty
is applied for off-topic noise keywords. The item is then bucketed:

- **High relevance** — score at or above the `high` threshold.
- **Worth a look** — score at or above the `medium` threshold.
- Below `medium` — dropped.

The themes reflect where tech news intersects DLG's work: generative AI and
agents (LuxuryIQ ships as an MCP server), search and answer engines (the GEO
practice), social and content platforms, e-commerce and the luxury resale
market, adtech and measurement and privacy, named luxury brands and groups,
China and APAC, and immersive formats. Tune any of this by editing the JSON; no
code change is needed.

The scorer decides *which* stories surface and gives a first-pass angle. The
sharper, headline-specific analysis is written by Claude via the skill, which
reads the JSON output.

## Network note

Some managed and web environments block `techmeme.com` at the network policy
layer (the fetch returns a proxy 403). That is expected and must not be routed
around. When it happens:

1. Run the tool where Techmeme is reachable (a local machine or a session whose
   network policy allows it), or
2. Save a feed and pass it with `--input`.

The tool tries `https://www.techmeme.com/feed.xml` first and falls back to the
`/m/` page, then exits with a clear message if neither is reachable.

## Scheduling

To get the brief on a cadence, wire `python3 techmeme_dlg.py` into whatever
scheduler runs where Techmeme is reachable (cron, a Claude Code routine, a CI
job), and route the output to email, Slack, or a Notion page.
