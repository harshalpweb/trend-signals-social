---
name: instagram-caption
description: Write the caption + hashtags for a TrendRadar post, given a content angle from instagram-signals and the post type (signal/no_signal/digest/build_in_public). Use once per post during the content-generation routine, after instagram-signals and before/alongside instagram-carousel.
---

# Write a TrendRadar Caption

## Voice

Match the account's established voice:

> "We track real search trends, marketplace bestsellers, and India's festival calendar to catch what's moving before everyone else notices. No guesswork. Just the numbers."

Short sentences. Confident but not hyped. Every claim traceable to an actual number from `instagram-signals` — never invent a stat.

**Human-voice check (mandatory before finalizing any caption or exemplar):** run the
mechanical AI-tell check in this repo's `CLAUDE.md` against the caption text. Em-dash
budget is 0 for a short social caption; avoid "X, not (just) Y" tails, "isn't X — it's
Y" antitheses, and staccato-tricolon-plus-"Just X" resolutions; never use "quietly" or
"actually." (Corrected 2026-08-25 — the previous exemplar quoted here was itself the
worst-scoring AI-tell offender in the account's history and had propagated its tells
into every caption written since; see `income-engine/docs/consults/2026-08-25-cco-ai-
tell-writing-audit.md`.)

## By post type

- **no_signal** (any signal slot with zero eligible entities, per `instagram-signals`' freshness gate, added 2026-08-28): Report the quiet cycle with real numbers — how many entities were scored, how many cleared the bar, what the bar is. "We checked 33 categories today. Nothing crossed our bar." is the whole shape. No entity is featured, no movement is claimed, and never dress the cycle up as a finding. This post type exists so a dry cycle produces honest content instead of a stretched claim; it should read like a lab notebook entry, not an apology.
- **signal** (Mon/Wed/Fri): Lead with the entity and the number, in one punchy line. Check `agreeing_families` from instagram-signals before writing any corroboration claim: if it has 2+ entries, naming them is genuine "receipts" proof — make it visible. **If it has only 1 entry, do not write "signals agree," "confirmed across sources," or similar plural-corroboration language** — attribute the single real source instead ("per Google Trends search data"). A false corroboration claim would undermine the account's entire premise; a single honest source is still a real, defensible claim. End with a genuine question (prediction-poll style, per `instagram-growth/references/psychology.md` §4) — e.g. "Seeing this in your category too?" — not generic engagement-bait.
- **digest** (Sat): Leaderboard framing — "This week's top movers:" followed by the 3-5 entities pulled by instagram-signals, each with its number. Close with a light forward-look, staying inside the `forward_dated_predictions: false` gate (frame as "worth watching," not "we predict").
- **build_in_public** (Sun): Methodology/process content — what the engine actually does, a build update, or an honest limitation being worked on. This is the one post type that doesn't need a signal pull.

## Hashtags

Max 5 (per `instagram-growth/config.yaml` `max_hashtags`). Mix broad (#TrendSpotting, #DataDriven) with niche/category-specific ones relevant to that week's entity. Never generic engagement-bait tags (#followforfollow, #like4like) — see `instagram-growth` Don'ts.

## Honesty check before finalizing

Re-read the caption against the numbers from `instagram-signals`. If a claim can't be traced to an actual `composite`/`conviction`/`momentum` value or a real festival date, cut it or soften it. This check matters more than punchiness — a single visibly wrong claim undermines the entire "receipts" premise for every post after it.

## Output

Write the final caption text (including hashtags) directly into that post's queue JSON `caption` field — see `content/queue/TEMPLATE.json`.
