---
name: instagram-carousel
description: Turn a content angle (from instagram-signals) and caption (from instagram-caption) into an on-brand, self-critiqued carousel of PNG slides ready to queue. Use for every weekly post. Wraps the Canva MCP tools plus the canva:get-design-feedback and canva:brand-check plugin skills — do not reimplement critique logic here, call those.
---

# Generate a TrendRadar Carousel

## The master template

There is no formal Canva "Brand Kit" for this account — the Canva plugin's MCP tools have no API to create one (`list-brand-kits` and `search-brand-templates` both return empty, and there is no create-brand-kit tool). Instead, brand consistency comes from a **master template design**, copied and edited each week:

- **Design ID: `DAHSjFtuvnU`** ("Premium Weekly Trend Report Cover"), view: `https://www.canva.com/d/3J_392N-M0vMkzb`
- Filed in the **`TrendRadar`** Canva folder (`FAHSjORWXy8`, `https://www.canva.com/folder/FAHSjORWXy8`)
- Locked 2026-08-17, matching the visual identity already live in the account's first post (`content/posted/2026-08-17-build-in-public-01`): dark navy-teal gradient background, single bright teal accent (~`#2FE0C4`), globe-icon + "TrendRadar" wordmark, thin divider lines, two-column footer.

**Before relying on any element ID below, re-run `start-editing-transaction` on `DAHSjFtuvnU` and check the returned `richtexts`/`fills` — Canva element IDs can shift if the design is manually edited in the UI. Treat the map below as a starting point, not gospel.**

Element map (as of 2026-08-17, page 1):

| Role | Element ID | Type |
|---|---|---|
| Wordmark "TrendRadar" | `PB4XfbSw4LCC234t-LBynVfp2X6xLD8Mx` | text |
| Headline (post title) | `PB4XfbSw4LCC234t-LByRFT0bqLypb8X8` | text |
| Subhead | `PB4XfbSw4LCC234t-LBmlhR5m1d05vxbp` | text |
| Main content box (chart/number/graphic goes here) | `PB4XfbSw4LCC234t-LBPDdxWR299PDC1n` | image fill, 748x457 |
| Footer left column text | `PB4XfbSw4LCC234t-LBmKWH981pRxNNcs` | text (widened to 300px — don't let it revert to the narrow default or long text will wrap character-by-character) |
| Footer right column text | `PB4XfbSw4LCC234t-LBcLCD8494LgrmZV` | text (widened to 300px, same caveat) |
| Footer divider line | `PB4XfbSw4LCC234t-LBtDh0rBg4CTVltg` | image |
| Globe icon | `PB4XfbSw4LCC234t-LBh3vwM95jcLyhZR` | image |

## Weekly generation steps

1. **Copy the master** — `copy-design` on `DAHSjFtuvnU` once per slide needed (5-7 per carousel, per `instagram-growth/config.yaml`). Each copy becomes one slide.
2. **Edit each copy** via `start-editing-transaction` → `perform-editing-operations` → `commit-editing-transaction`:
   - Slide 1 (hook): headline = the curiosity-gap hook (from `instagram-caption`), subhead = post-type label ("This Week's Signal" / "Weekly Digest" / "Build in Public"), footer columns = a short stat teaser + "swipe →".
   - Data slides: headline = the entity/number from `instagram-signals`, main content box = a chart/number graphic (`insert_fill` or `update_fill` with an uploaded asset — see `upload-asset-from-url` — or a simple large-number text treatment if no chart asset is warranted), footer = source citation (small, always present — see `instagram-growth/references/design-trends.md` §4).
   - Closing slide: headline = CTA ("Follow for weekly signals" or similar, matching the account's established voice), footer = "Data-backed." / "Not hype." (the locked tagline) or a swap-in relevant to that week.
   - Keep 1-2 sentences max per slide (per `instagram-growth` rules) — this is not a report.
3. **Export each slide**: `get-export-formats` for the design first (required before `export-design`), then `export-design` with `type: png`, full resolution (1080 width). `export-design` returns a signed download URL, not a file — download it (e.g. `curl -sL "<url>" -o content/queue/slides/{scheduled_date}-{slug}-{n}.png`) into this repo; the URL itself is not what goes in the queue JSON.
4. **Self-critique gate** (this is what makes it "top notch," not just generated):
   - Run `canva:get-design-feedback` on the carousel.
   - If it flags hierarchy, readability, consistency, or accessibility issues: apply fixes via `canva:edit-design` (or the same `perform-editing-operations` flow above).
   - Re-check. **Up to 2 revision passes.**
   - If still failing after 2 passes: queue it anyway, but set `"needs_review": true` in that post's queue JSON (extend the schema — see `content/queue/TEMPLATE.json` in this repo's root) so it surfaces for the founder's optional spot-check instead of silently shipping a flawed post.
5. **Brand check**: run `canva:brand-check` before queueing to catch any color/font/logo drift from the master template.

## Don't regenerate from scratch each week

`generate-design` (the AI generator) produced 4 candidates before landing on the current master, including one with a garbled fake-UI-mockup background — AI generation from a text prompt is unreliable for exact brand consistency. Always start from the locked master template (`copy-design`) rather than calling `generate-design` again, unless the founder explicitly asks for a redesign.
