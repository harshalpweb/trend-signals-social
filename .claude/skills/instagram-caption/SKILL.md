---
name: instagram-caption
description: Write the caption + hashtags for a TrendRadar post, given a content angle from instagram-signals and the post type (signal/digest/build_in_public). Use once per post during the weekly routine, after instagram-signals and before/alongside instagram-carousel.
---

# Write a TrendRadar Caption

## Voice

Match the account's established voice (see the live first post, `content/posted/2026-08-17-build-in-public-01/*.json`):

> "We track real search trends, marketplace bestsellers, and India's festival calendar to spot what's about to blow up — before it does. No guesses. No hype. Just signals."

Short sentences. Confident but not hyped. Every claim traceable to an actual number from `instagram-signals` — never invent a stat.

## By post type

- **signal** (Mon/Wed/Fri): Lead with the entity and the number, in one punchy line. State which signal families agree (`agreeing_families` from instagram-signals) — this is the "receipts" proof, make it visible, not buried. End with a genuine question (prediction-poll style, per `instagram-growth/references/psychology.md` §4) — e.g. "Seeing this in your category too?" — not generic engagement-bait.
- **digest** (Sat): Leaderboard framing — "This week's top movers:" followed by the 3-5 entities pulled by instagram-signals, each with its number. Close with a light forward-look, staying inside the `forward_dated_predictions: false` gate (frame as "worth watching," not "we predict").
- **build_in_public** (Sun): Methodology/process content — what the engine actually does, a build update, or an honest limitation being worked on. This is the one post type that doesn't need a signal pull.

## Hashtags

Max 5 (per `instagram-growth/config.yaml` `max_hashtags`). Mix broad (#TrendSpotting, #DataDriven) with niche/category-specific ones relevant to that week's entity. Never generic engagement-bait tags (#followforfollow, #like4like) — see `instagram-growth` Don'ts.

## Honesty check before finalizing

Re-read the caption against the numbers from `instagram-signals`. If a claim can't be traced to an actual `composite`/`conviction`/`momentum` value or a real festival date, cut it or soften it. This check matters more than punchiness — a single visibly wrong claim undermines the entire "receipts" premise for every post after it.

## Output

Write the final caption text (including hashtags) directly into that post's queue JSON `caption` field — see `content/queue/TEMPLATE.json`.
