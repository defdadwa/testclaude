# CLAUDE.md

Guidance for AI assistants working in this repository.

## What this is

A single-page marketing landing site for **LuxuryIQ MCP**, a hosted MCP
(Model Context Protocol) server that preloads luxury-market intelligence into
AI assistants (ChatGPT, Claude, Copilot). The site pitches the product, its
seven data sources, business-impact examples, and pricing tiers, ending in a
contact/CTA section.

This is a static site. There is no build step, no framework, no package
manager, no backend, and no tests. It is three hand-authored files served
directly to the browser.

## File structure

- `index.html` — all page markup and content. Single scrolling page with
  anchor-linked sections: nav, hero (with an animated chat demo), problem/
  solution comparison, seven database cards, stats, business-impact cards,
  implementation steps, pricing, CTA, footer.
- `styles.css` — all styling (~1385 lines). Organized top-to-bottom by
  section with `/* ===== Section Name ===== */` banner comments. Design
  tokens live in `:root` at the top.
- `script.js` — all interactivity (vanilla JS, no dependencies). Entry point
  is a single `DOMContentLoaded` handler that calls the init functions.

## Running and previewing

Open `index.html` directly in a browser, or serve the directory:

```
python3 -m http.server 8000    # then visit http://localhost:8000
```

External runtime dependencies are loaded from CDNs at page load: Google Fonts
(Inter and Playfair Display). There is nothing to install or compile.

## Conventions

### CSS
- Use the design tokens in `:root` rather than hard-coded values. Key ones:
  - Backgrounds: `--color-bg-primary` (#0a0a0f) through `--color-bg-card`.
  - Accents: `--color-accent-gold` (#c9a962) is the primary brand color;
    `--color-accent-purple`, `--color-accent-blue` are secondary.
  - Gradients: `--gradient-gold`, `--gradient-premium`, `--gradient-subtle`.
  - Text: `--color-text-primary/secondary/muted`.
  - Also `--shadow-*`, `--font-primary` (Inter), `--font-display` (Playfair),
    `--section-padding`, `--container-width` (1200px), `--transition-*`.
- The theme is a dark luxury palette with gold accents. Headings use the
  Playfair Display serif; body uses Inter.
- The `.gradient-text` class applies the gold gradient to inline text (used
  for emphasized words inside headings).
- Layout width is constrained by `.container` (max `--container-width`,
  centered, 24px side padding).
- When adding a new section, place its styles under a new `/* ===== ... ===== */`
  banner in the same source order as the section appears in `index.html`.
- Responsive breakpoints are the three `@media` blocks at the bottom of the
  file: max-width 1024px, 768px, and 480px. Add responsive overrides there,
  not scattered inline.

### HTML
- Sections are wrapped in `<section>` with an `id` when they are anchor
  targets (`#features`, `#databases`, `#impact`, `#pricing`, `#contact`).
  Nav links and CTAs point at these ids.
- Inline SVGs (stroke-based, `viewBox="0 0 24 24"`) are used for all icons.
  Match this pattern for new icons rather than adding an icon library.
- Repeated card patterns (`.database-card`, `.impact-card`, `.pricing-card`)
  share structure. Copy an existing card as the template when adding one.

### JavaScript
- Vanilla JS only. No frameworks, no bundler, no dependencies.
- All features are initialized from the `DOMContentLoaded` handler at the top
  of `script.js`. Add a new feature as a named `initX()` function and call it
  from there.
- Existing behaviors: navbar scroll state (`initNavbar`), smooth anchor
  scrolling with an 80px header offset (`initSmoothScroll`), IntersectionObserver
  scroll-reveal animations and animated stat counters (`initScrollAnimations`
  / `animateStats`), mobile menu toggle (`initMobileMenu`), and the hero chat
  typing effect (`initTypingEffect`). There is also a scroll parallax on the
  hero background and JS-driven card hover lift near the bottom.
- Some CSS is injected from JS at runtime (mobile-menu styles in
  `initMobileMenu`, the `.visible` reveal class in `initScrollAnimations`).
  Be aware these rules do not live in `styles.css`.
- Animated stat numbers read their target from the `data-count` attribute on
  `.stat-number` and append a `+` if the original text contained one.

## Content notes

Per DLG data-integrity standards, treat every statistic, percentage, and
ranking in the copy (engagement rates, brand counts, spend figures, etc.) as
marketing illustration. Do not present these numbers as verified data, and do
not invent new figures. If asked to add real metrics, source them and flag
estimates explicitly.

Brand voice is premium and restrained: precise, product-rooted language.
Avoid "luxurious" as a descriptor and the usual filler adjectives.

## Git workflow

- The repository's default branch is `claude/luxuryiq-landing-page-bmtmZ`.
- Commit with clear, descriptive messages. Keep changes scoped to the three
  source files unless the task requires new assets.
- Do not open a pull request unless explicitly asked.
