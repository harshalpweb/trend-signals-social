---
name: instagram-growth
description: Research-backed Instagram growth playbook for @trendradar.in — how to pick hooks, format carousels, choose posting times, decide content mix, and what NOT to do. Use when generating weekly content or making any strategic call about the account (cadence, tone, format, trend-jacking). Not for one-off design questions — see instagram-carousel for execution.
---

# TrendRadar Instagram Growth Playbook

This is the account's strategic brain — read it before generating a week's content, not just once. It exists so a fresh session can act on the account's growth strategy without the founder re-explaining anything.

Positioning: **"receipts engine"** — real trend signals, not generic inspiration/hype content. Every tactic below is filtered through one test: *does this build or erode credibility?* When a growth tactic conflicts with that, credibility wins. See `references/` for the full cited research behind each rule.

## Config knobs (founder-tunable, everything else runs automatically)

See `config.yaml` in this folder. Do not hardcode these values elsewhere — read them at generation time so the founder can tune the account without touching skill logic.

## Format & cadence

- **Static image carousels only** for now, not Reels — reliable to automate, and in the education/data niche specifically, carousels edge out Reels on engagement rate (~0.55% vs ~0.52%, per the case-study research — not a universal Instagram-wide benchmark, treat as directional). Revisit Reels once the carousel pipeline has run reliably for several weeks. [references/case-studies.md]
- **5-7 slides per carousel** is the sweet spot for data-reveal content. Below 5, not enough room for a hook + payoff + depth; above 7-8, completion rate drops. [references/design-trends.md]
- **5 posts/week**, not daily: Mon/Wed/Fri = trend-signal carousels, Sat = weekly digest/leaderboard, Sun = build-in-public/methodology. Daily posting was explicitly rejected as a vanity metric that dilutes the "receipts" identity with filler.
- **Posting window**: aim for evening IST (roughly 7-9pm), which aggregate creator data suggests is peak India activity — but this is *not* Meta-official data. [confirmed vs speculative — see references/algorithm.md §5] Once the account has 2+ weeks of its own Insights data, switch to that instead of the aggregate default — it's more predictive than any external benchmark.
- **5 hashtags max per caption.** More than that gets treated as spam-adjacent by the ranking system. [references/algorithm.md §4]

## The hook (slide 1) is most of the battle

- Never reveal the insight on slide 1 — open a curiosity gap the swipe resolves. E.g. "We found 1 metric most founders miss — swipe" not "Here's the metric." [references/psychology.md §2]
- Slide 1 needs to work in under 2 seconds: bold headline, high contrast, one clear visual. If a viewer scrolls past without engaging, Instagram gives carousels a rare "second chance" re-serve using slide 2 as the new entry point — so slide 2 should also be able to stand alone as a hook. [references/algorithm.md §1, §3 — tagged confirmed/Mosseri]
- Curiosity-gap framing must stay honest. "We tracked this for 6 months, here's what shifted" is fine. Fake urgency ("This just happened!" when it didn't) or exaggerated claims are explicitly off-limits — see Don'ts.

## What makes data content genuinely shareable (not just likeable)

- Optimize for **saves**, not likes. Saves signal "reference-quality" content and outrank likes in distribution weight — this is the correct metric for a receipts-style account, not a consolation prize. [references/psychology.md §3]
- Design for saves: clean typography, one stat per slide, visible source citation (small but always present — its absence reads as a missing trust signal, not a neutral omission). [references/design-trends.md §4]
- DM shares ("sends per reach") carry the highest weight for reaching non-followers of any single signal. Frame content so it's the kind of thing someone forwards to a specific person ("this is exactly what you were asking about"), not just broadcasts. [references/algorithm.md §1, confirmed]
- Genuine comment-bait that fits the brand: prediction polls ("which of these surprises you most?"), not generic "comment below!" spam. [references/psychology.md §4]

## Visual execution (feeds instagram-carousel)

- Dark editorial aesthetic (matches the account's existing look: deep navy/teal background, single bright teal accent, no other bright colors) outperforms bright/playful templates for a data-credibility brand. [references/design-trends.md §3]
- One accent color only, used consistently for headlines, data highlights, and dividers — grey/muted tones for everything else. [references/design-trends.md §3]
- Minimum 24pt-equivalent body text, 1-2 sentences per slide max — this is a phone-screen medium, not a report. [references/design-trends.md §5]
- Full execution detail (fonts, master template, element structure) lives in the `instagram-carousel` skill — this section is the strategic "why," not the how.

## What NOT to do (hard rules, not preferences)

- **No bought followers, engagement pods, follow/unfollow trains, or bot activity** — ToS-violating, and several fast-growth case studies that used these got explicitly flagged as "avoid" despite raw numbers. [references/case-studies.md]
- **No forward-dated "we called it before it happened" posts** until the engine's lead time is privately validated — a visible wrong call would undermine the entire "receipts" premise. This is a standing gate, not a one-time decision; check with the founder (or trend_predictor's validated-lead-time status) before lifting it.
- **No exaggerated/cherry-picked claims, no fake urgency.** Authenticity outperforms hype for this positioning, and any gap between claim and evidence shows up in replies and destroys long-term authority. [references/psychology.md §5]
- **No hashtag spam** (5 max), no reposted/watermarked content — both are known suppression triggers. [references/algorithm.md §4]

## Future work (explicitly not built yet)

Performance-feedback loop (reading real post performance via Instagram Insights and feeding it back into content decisions) is deliberately not built. Founder said "not now." Don't build it without being asked — but don't design anything here in a way that would need to be undone to add it later (e.g. keep post metadata in the queue JSON rich enough that a future loop could read `ig_post_id` and correlate).
