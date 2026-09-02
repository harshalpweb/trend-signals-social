---
name: instagram-carousel
description: Turn a content angle (from instagram-signals) and caption (from instagram-caption) into an on-brand, self-critiqued carousel of PNG slides ready to queue. Use for every weekly post. Wraps the Canva MCP tools plus the canva:get-design-feedback and canva:brand-check plugin skills — do not reimplement critique logic here, call those.
---

# Generate a TrendRadar Carousel

**SUPERSEDED 2026-08-29 — read `scripts/render_html/README.md` first.**
The founder rejected this template's visual output outright ("looks
very bad") and a full redesign process (2 research rounds + 3
prototypes, `docs/consults/2026-08-29-group-cto-instagram-trendy-design-round1.md`
and `-round2-selection.md` in the `income-engine` repo) replaced it
with the cream/ink/marigold "Bazaar Receipt" system. That system's
live implementation is the **HTML/Playwright renderer**
(`scripts/render_html/`, this repo) — an intermediate Pillow renderer
(`scripts/render/`) was itself superseded for new content (glyph-size
defect; see the render_html README) and stays only as history. Neither
is a Canva master template — the empty-content-box problem this file
describes below was never actually about missing infrastructure
(`raw.githubusercontent.com` slide hosting already existed the whole
time); it just wasn't discovered until the redesign forced a real
look. **The account is also renamed TrendGiri, not TrendRadar**
(`docs/consults/2026-08-26-trendgiri-rename-checklist.md`) — every
"TrendRadar" reference below is stale.

This file is kept for its still-accurate Canva-mechanics knowledge
(export flow, the AI-generator unreliability finding, the critique-gate
pattern) in case a future decision moves generation back onto Canva —
but do not copy `DAHSjFtuvnU` or follow the element map below for new
content. Use `scripts/render_html/` per its README instead.

## Original content (Canva master-template approach, historical)

## The master template

There is no formal Canva "Brand Kit" for this account — the Canva plugin's MCP tools have no API to create one (`list-brand-kits` and `search-brand-templates` both return empty, and there is no create-brand-kit tool). Instead, brand consistency comes from a **master template design**, copied and edited each week:

- **Design ID: `DAHSjFtuvnU`** ("Premium Weekly Trend Report Cover"), view: `https://www.canva.com/d/3J_392N-M0vMkzb`
- Filed in the **`TrendRadar`** Canva folder (`FAHSjORWXy8`, `https://www.canva.com/folder/FAHSjORWXy8`)
- Locked 2026-08-17, matching the visual identity already live in the account's first post (`content/posted/2026-08-17-build-in-public-01`): dark navy-teal gradient background, single bright teal accent (~`#2FE0C4`), globe-icon + "TrendRadar" wordmark, thin divider lines, two-column footer.
- **Revised 2026-08-17 (same day, first-week fix)**: the template originally had a large empty "content box" (meant for a chart/number graphic) that was never actually filled by any generation pass, because `perform-editing-operations` has no operation to insert a *new* text element — only `replace_text`/`format_text` on existing ones, `update_fill`/`insert_fill` for image/video, and `delete_element`/`position_element`/`resize_element`. Filling it with a real chart would require generating a chart image externally and hosting it somewhere `upload-asset-from-url` can fetch — infrastructure that doesn't exist yet. It shipped empty on the account's very first live post and looked like a broken placeholder. **The content box has been deleted from the master template** and the footer/divider repositioned up to close the gap (footer top ≈513, divider top ≈488/height 80, matching the subhead's bottom + ~85px). Every future `copy-design` off `DAHSjFtuvnU` inherits this fix automatically — do not reintroduce a content box unless it's actually going to be filled with real content in the same pass.

**Before relying on any element ID below, re-run `start-editing-transaction` on `DAHSjFtuvnU` and check the returned `richtexts`/`fills` — Canva element IDs can shift if the design is manually edited in the UI. Treat the map below as a starting point, not gospel.**

Element map (as of 2026-08-17, post-fix, page 1):

| Role | Element ID | Type |
|---|---|---|
| Wordmark "TrendRadar" | `PB4XfbSw4LCC234t-LBynVfp2X6xLD8Mx` | text |
| Headline (post title) | `PB4XfbSw4LCC234t-LByRFT0bqLypb8X8` | text |
| Subhead | `PB4XfbSw4LCC234t-LBmlhR5m1d05vxbp` | text |
| Footer left column text | `PB4XfbSw4LCC234t-LBmKWH981pRxNNcs` | text (widened to 300px, top≈513 — don't let width revert to the narrow default or long text will wrap character-by-character) |
| Footer right column text | `PB4XfbSw4LCC234t-LBcLCD8494LgrmZV` | text (widened to 300px, top≈513, same caveat) |
| Footer divider line | `PB4XfbSw4LCC234t-LBtDh0rBg4CTVltg` | image, top≈488, height 80 |
| Globe icon | `PB4XfbSw4LCC234t-LBh3vwM95jcLyhZR` | image |

**There is no content box anymore.** If a future iteration wants a real chart/number visual, that needs new infrastructure (generate a chart image, host it somewhere fetchable, `upload-asset-from-url` it in) — don't add an empty placeholder box back as a shortcut.

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
