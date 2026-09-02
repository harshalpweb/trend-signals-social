# TrendGiri Pillow render system

Produces the "Bazaar Receipt" visual system directly with Pillow —
built 2026-08-29 as a fast, precise alternative to fighting Canva's
editing API for pixel-exact charts, stamps, and rotated receipts. See
`docs/consults/2026-08-29-group-cto-instagram-trendy-design-round2-selection.md`
in the `income-engine` repo for the design spec and rationale this code
implements.

**SUPERSEDED for new content (2026-08-29, committed 2026-09-02):** the
live pipeline is `scripts/render_html/` (HTML/Playwright) — this Pillow
system shipped every glyph at half the specified size (see
`income-engine/docs/consults/2026-08-29-group-cto-typography-diagnostic-pass1.md`
and `scripts/render_html/README.md`). This directory stays as history:
the founder-review samples it produced are reproducible from it, and
the receipt/chart/stamp construction patterns remain a useful
reference. Do not produce new content with it.

## Files

- `base.py` — low-level Pillow primitives (fonts, 2x-supersampled
  canvas, text/line/circle helpers, `S()` coordinate scaling). Palette-
  agnostic; also carries the earlier dark "data dashboard" system,
  superseded but left in place since some helpers are still shared.
- `giri_system.py` — the actual Bazaar Receipt system: cream/ink/
  marigold palette, the receipt-strip + stamp construction (stamps
  must never occlude a data value — see the round-2 consult for why), clean
  (non-wobbled) chart primitives, Caveat hand-annotation helper.
- `giri_compose.py` — the 4-deck, 30-slide TrendGiri rebuild
  (2026-08-29): signal, digest, build-in-public, and the first seller-
  wisdom attempt. Kept as a working reference for the receipt/chart/
  stamp patterns, even though deck 4 there was superseded by
  `giri_lanes.py`'s broader rebuild.
- `giri_lanes.py` — the 3 new-lane samples (2026-08-29, second round):
  Bazaar Bulletin (news), Seller Wisdom v2 (broadened per the niche
  taxonomy), Seller Playbook.

## Fonts

`../../assets/fonts/` — all genuinely open-source (OFL/Apache) Google
Fonts, safe to redistribute in this repo: Space Grotesk, IBM Plex Mono,
Inter, Anton, Archivo Black, Caveat, Permanent Marker.

## Running

```
cd scripts/render
py -3 -c "import giri_lanes as L; L.b_s1()"   # render one slide
py -3 giri_lanes.py                            # render everything in the file
```

Output paths are hardcoded per-script to their own dated
`content/samples/<date>-<slug>/` directory — these are dated content
batches, not a general-purpose CLI. Copy the pattern into a new script
for the next batch rather than parameterizing this one.

## Known gaps, honestly

- No automated test coverage. Verification so far has been visual (the
  Read tool viewing each rendered PNG) plus manual bug-hunting — real
  bugs were found and fixed this way (stamps occluding data, a missing
  font glyph rendering as a stray mark, a dashed line visually cutting
  through a circle marker). See git history same-day for the fix
  commits.
- No `check_repetition.py` integration yet — the content-ledger anti-
  repetition mechanism (`docs/consults/2026-08-29-group-cto-trendgiri-niche-and-content-strategy.md`
  §2.4) is designed but not built. If it lands, it gates *before* any
  compose script runs, not inside this module.
- Not wired into `publish_due_posts.py` or the scheduled task. These
  scripts are run by hand, output reviewed, then committed. Wiring
  this into the actual unattended pipeline is a separate decision.
