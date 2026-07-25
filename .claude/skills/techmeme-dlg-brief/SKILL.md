---
name: techmeme-dlg-brief
description: Build a DLG / LuxuryIQ relevance brief from Techmeme. Use whenever the user wants to know what is worth their attention on Techmeme (https://www.techmeme.com/m/), asks for a tech-news scan through a DLG or LuxuryIQ lens, or invokes /techmeme-dlg-brief. Runs the news/techmeme_dlg.py scorer to filter the river, then writes a short so-what and one concrete idea for each item that clears the bar. Skips analysis on anything that does not clear it.
---

# Techmeme brief for DLG / LuxuryIQ

Turn the Techmeme river into a short list of what actually matters to Digital
Luxury Group and LuxuryIQ, with a headline-specific angle and one actionable
idea per item. Analysis appears only where a headline is genuinely relevant.

## How it works

A deterministic scorer (`news/techmeme_dlg.py`, config in
`news/relevance_config.json`) decides *which* headlines survive and gives a
first-pass theme angle. You add the judgment: a tight so-what and one concrete
suggestion tied to the specific headline, not a generic restatement.

## Steps

1. Get the relevant items as JSON:

   ```bash
   python3 news/techmeme_dlg.py --format json
   ```

   For only the top bucket, add `--min high`. To cap the list, add `--limit N`.

2. If the live fetch fails with a Techmeme reachability / 403 error, the current
   environment blocks techmeme.com at the network policy. Do not route around
   it. Either run this where Techmeme is reachable, or ask the user for a saved
   feed file and pass it with `--input path/to/file.xml`. A sample fixture lives
   at `news/sample_feed.xml` for testing the pipeline offline.

3. For each item in `kept`, write the brief. Use the JSON's `dlg_angle` and
   `idea` as a starting point, then sharpen to the actual headline:
   - **Why it matters** — one or two sentences on the concrete consequence for
     DLG's work or LuxuryIQ, specific to this story.
   - **Idea / suggestion** — one action worth taking: a client to flag, an audit
     or product check, a proof point to reuse. Omit if there is genuinely no
     action, rather than padding.
   Group as High relevance and Worth a look, mirroring the JSON `bucket`.

4. Lead with the single most important item or the through-line across the set,
   then the list. Keep the whole brief to a page unless asked for more.

## House style (DLG)

- Prose by default. Bullets only when structure genuinely helps.
- No em dashes. Do not use: delve, elevate, leverage, navigate, dive deep,
  harness the power of, "it's not just X, it's Y", "in today's fast-paced".
- Name the source for every claim; never invent rankings, numbers, or brand
  facts. If a headline is thin, say what is unconfirmed rather than filling it in.
- English by default.

## Tuning

Relevance is fully in `news/relevance_config.json`: theme weights, keyword sets,
the high/medium thresholds, per-theme DLG angle and idea seeds, and a noise list
that penalises off-topic infrastructure and crypto stories. Edit that file to
change what surfaces; no code change needed.
