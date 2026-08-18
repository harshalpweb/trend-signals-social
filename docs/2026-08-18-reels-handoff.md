# Reels for @trendradar.in — investigation + handoff (2026-08-18)

Status: **investigated, design agreed in principle, paused** so the founder can restart
Claude Code with browser access (`claude --chrome`). Nothing built yet. This doc lets a
fresh session pick up without re-deriving anything. Memory pointer:
`project-trendradar-reels` in the trend_predictor Claude memory.

## 1. What was asked

Founder: "look into creating reels for our channel using canva" → then "I have bought a
Pro plan and you say you can't make videos?" → "if I give you browser access can you do
that?" → "so many apps in Canva, can you access them via API? also the AI chatbot?"

Prior on-record decision (`.claude/skills/instagram-growth/SKILL.md`): carousels-first,
"revisit Reels once the carousel pipeline has run reliably for several weeks". Pipeline
has run exactly one week (first batch queued 2026-08-17). Treat Reels as an **experiment**
alongside carousels, not a pivot — unless the founder decides otherwise (see §5).

## 2. Verified findings (each checked live or against canva.dev, not assumed)

| Question | Answer | Evidence |
|---|---|---|
| Can the Canva API make a video file? | **Yes.** `export-design` supports `mp4`. | Exported master `DAHSjFtuvnU` with `{type: mp4, quality: vertical_1080p, export_quality: pro}` → job success, 5.0 s H.264 clip, ~88 KB (static page, no audio). `get-export-formats` on that design lists `mp4`. |
| Can the API author animation / music / transitions / page duration? | **No.** No operation exists for any of these. | `perform-editing-operations` schema: only text replace/format, media `update_fill`/`insert_fill`, delete/position/resize, autofill mapping. `generate-design` has no video/reel design type (closest: `your_story` = 9:16 static). |
| Can the API put video into a page? | **Yes**, `insert_fill` / `update_fill` with `asset_type: video` — but the asset must first be uploaded via `upload-asset-from-url` from a **public** URL (no stock-video search in the MCP). | Tool schemas. |
| Are Canva marketplace apps callable via API? | **No.** Apps are Apps-SDK plugins that run inside the editor UI. Connect API (what the MCP wraps) is a separate, narrower surface: designs, assets, autofill, exports, folders, comments, brand kits. | canva.dev: Connect APIs docs, Apps SDK docs. |
| Is Canva AI / Magic Media (text-to-video, Magic Animate, Magic Write…) callable via API? | **No — UI only.** The only Canva-AI feature exposed is `generate-design` (prompt → candidates → editable design; takes `brand_kit_id`). | canva.dev + multiple 2026 reviews ("no API access for automation"). |
| What did Canva Pro (bought 2026-08-18) change? | Pro-quality MP4 export now works (verified). Brand Kit creation possible in UI (currently empty: `list-brand-kits` → `[]`). Premium animations, music library, premium stock video, Magic Media (Veo 3, ≤8 s clips w/ synced audio) — all UI. | Live checks + docs. |
| Can Instagram publish it? | **Yes.** Graph API: create container `media_type=REELS`, `video_url=<public mp4>`, poll status until `FINISHED`, then publish. `raw.githubusercontent.com` serves MP4 (<100 MB; ours ≈10–30 MB). | `scripts/publish_due_posts.py` already implements the container-poll/publish pattern for carousels — extension is small. |
| Browser access from Claude Code? | **Yes.** Claude Code 2.1.234 has `--chrome` (Claude in Chrome integration, drives the founder's own logged-in Chrome). The `browser-use` plugin MCP is installed but fails to connect — not worth debugging. | `claude --help`, `claude mcp list`. |

## 3. Agreed design (in principle — spec/plan still to be written via brainstorming)

Same trick that already gives brand consistency for carousels without a Brand Kit:
**a locked master carries the "DNA"; the automation only fills text and exports.**

1. **Reel master** — new locked design, 1080×1920, 5 pages, same text slots/element roles
   as carousel master `DAHSjFtuvnU` (hook / signal / receipt / context / CTA), same
   navy-teal identity. Created via API (`copy-design` + `resize-design` or fresh), then
   **once, in the Canva UI via Chrome**: page animations, a music track from the Pro
   library, page durations (~3–4 s → 15–20 s reel), optionally a Magic Media 8 s clip or
   premium stock loop as background. Every later `copy-design` inherits all of it.
2. **Weekly routine** (API only — runs headless via `TrendRadarWeeklyContent` scheduled
   task, so no browser in the loop): `copy-design` reel master → `replace_text` per page →
   self-critique gate (`canva:get-design-feedback` on the pages) → `export-design mp4`
   (`vertical_1080p`, `pro`) → download → commit to `content/queue/<id>/<id>.mp4` with
   the post JSON carrying `format: "reel"`.
3. **Publish** — `publish_due_posts.py`: branch on `format`; for `reel`: single container
   `media_type=REELS`, `video_url` = raw GitHub URL, `caption`, optional `cover_url` (a
   PNG export of page 1), poll `status_code == FINISHED` (can take 30–90 s), publish.
   Keep carousel path untouched.
4. **Brand Kit** (bonus, one-time in UI): navy/teal palette, fonts, globe wordmark →
   makes `generate-design brand_kit_id=…` a usable second generation path.
5. Cost: ₹0 marginal. Effort: master setup is a one-time browser session; code changes
   are one skill (new `instagram-reel` or extend `instagram-carousel`), publish-script
   branch, queue-schema field, scheduler allow-list check.

Constraints that must survive: no forward-dated "we called it" claims; honest single-source
framing (agreeing-family count gate); no generic inspiration content; 4–5 posts/week cap.

## 4. Resume checklist (for the next session)

- [ ] Founder restarts with `claude --chrome` (Claude in Chrome extension installed,
      Chrome logged into Canva Pro). Say "continue the reels work".
- [ ] **Ask the open decision first (§5).**
- [ ] Browser: create Brand Kit in Brand Hub (palette/fonts/logo from
      `.claude/skills/instagram-carousel/SKILL.md` element map).
- [ ] API: create Reel master (1080×1920, 5 pages) in the `TrendRadar` Canva folder;
      browser: add animation + audio + durations (+ optional Magic Media background);
      test-export MP4 and send to founder; lock/document element map in the skill.
- [ ] Brainstorm → spec (`docs/superpowers/specs/2026-08-XX-instagram-reels-design.md`
      in trend_predictor, matching the existing specs) → plan → implement with the usual
      haiku→sonnet→opus→fable ladder.
- [ ] First reel goes through the real hourly publish workflow; confirm in
      `content/posted/` before calling it done.

## 5. Open decision — founder has NOT answered yet

What role should Reels play?
- **A) Additive experiment (recommended)** — keep the 5 carousel slots; add 1 reel/week
  (Reel version of the Saturday digest) to compare reach vs carousels on the same content.
- **B) Replace some slots** — Mon/Wed/Fri become reels, Sat/Sun stay carousels.
- **C) Occasional / festival only** — e.g. Raksha Bandhan (2026-08-28), festival countdowns.

## 6. Artifacts from this session

- Test MP4 export of the master (proof of concept, no motion/audio): produced via
  `export-design`, sent to founder in-session; not committed (regenerable in one call).
