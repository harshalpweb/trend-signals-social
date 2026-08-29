# render_html — TrendGiri HTML/CSS slide renderer (Playwright)

Supersedes `scripts/render/` (Pillow). The Pillow system stays in place as
history but must not produce new content: its output shipped every glyph at
half the specified size (see
`income-engine/docs/consults/2026-08-29-group-cto-typography-diagnostic-pass1.md`).

## How it works

- `template.css` — the entire visual system. Type scale is LOCKED to 4
  tokens: display 112/1.04 (Anton, caps only), heading 58/1.12 (Anton, caps
  only), body 42/1.40 (Inter 400/500), meta 26/1.40 (IBM Plex Mono).
  Palette: cream `#F5EEE2`, ink `#1A1714`, ink-soft `#4A443B`, marigold
  `#FFB627` (background blocks only, always ink text on it), line `#C9BFA9`
  (hairlines only, never text). Every text/background pair in the sheet is
  >= 8:1 WCAG. Do not add sizes or pairs without a Group CTO review.
- `render_html.py` — deck JSON -> per-slide HTML -> headless Chromium at
  1080x1350 `device_scale_factor=2` -> LANCZOS downsample -> PNG.
  Slide roles: `hook`, `list`, `principle`, `quote` (dark), `closer`.
  Rich text: `[[...]]` = marigold highlight, `**...**` = medium weight.
  `--verify-shaping` proves browser kerning is active (measured deltas:
  Inter -100px, Anton -17px on the probe string vs `font-kerning: none`).
- `gate_check.py` — the pass-1 completion gate, mechanical form: type-token
  checks, WCAG contrast for every pair the CSS can produce, per-slide ink
  coverage (8-20% band), and 350px feed-scale previews written to
  `<deck>/_preview350/`. **Looking at the previews is still a mandatory
  human/agent step — the numbers do not replace eyes.**

## Usage

```
cd scripts/render_html
py -3 render_html.py decks/<deck>.json
py -3 gate_check.py ../../content/samples/<batch>/<slug>
```

Deck JSON goes in `decks/`; output lands in
`content/samples/<batch>/<slug>/slide-N.png` (+ `_html/` debug copies,
`_preview350/` feed-scale previews).

## Definition of done for any new deck

1. `gate_check.py` all-PASS (contrast, coverage band, tokens).
2. Every `_preview350/` image actually viewed at feed scale.
3. Caption passes `py -3 -m copydesk --caption <path>` (income-engine/copydesk).
4. No source-brand naming (standing Legal finding); no stale live-data claims.
