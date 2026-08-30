# WIP claim: Reels/animation build — Group CTO session (2026-08-30)

**Claim:** per direct founder instruction (relayed via CoS/income-engine-f6),
Group CTO is building the first Reel for this account today, plus the
cross-account Reels layer for the 3 `instagram-accounts-social` accounts.
Group CTO is the owning agent for the animation/music/Reels approach,
including TrendGiri — income-engine-69's scoped-but-unbuilt
gentle-animation/music/Reels proposal is being executed here, extending
(not replacing) `income-engine/docs/consults/2026-08-29-group-cto-trendgiri-niche-and-content-strategy.md`
§2.6 and `docs/2026-08-18-reels-handoff.md`.

**What this session will touch in this repo:**
- `scripts/render_html/render_reel.py` (new — frame-capture video renderer)
- `scripts/render_html/reels/` (new — reel HTML sources)
- `assets/audio/` (new — traced Mixkit-licensed audio + ATTRIBUTION.md)
- `scripts/publish_due_posts.py` (small edit — longer poll timeout for
  video containers only; carousel path untouched)
- one new queue entry `content/queue/2026-08-30-reel-*.json` (+ mp4)

**Not touched:** existing queue entries, batch2 posts, skills, the
uncommitted `scripts/render/` + `assets/fonts/` + `platforms/` +
`instagram-carousel/SKILL.md` working-tree changes (those belong to
another session's pending commit pass).

Delete this file when the build lands (same session).
