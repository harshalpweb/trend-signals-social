# Growth strategy work — pick up here next session

Status: not started (research was kicked off 2026-08-17 then explicitly cancelled by
the founder mid-run — "dont research and all now" / "Do it later"). This doc exists so
a fresh session has the full task without re-deriving it.

## What the founder wants (their words, paraphrased)

"Eventually I want you to handle my Instagram brilliantly... come up with strategies
[like accounts that hit 500k followers in 60 days]... I should just be involved to
change configs or so, rest all should be automatic."

Concretely:
1. Build a persistent, research-backed Instagram growth strategy — not generic advice,
   grounded in (a) how Instagram's algorithm actually distributes content, (b) the
   psychology of what makes people share/save/comment, (c) what genuinely drove
   documented fast-growth accounts (honestly separating real mechanisms from
   survivorship bias or against-ToS tactics that would risk this account).
2. Package it as something any future session can pick up and act on autonomously —
   structure it as a proper Claude Code **skill** (SKILL.md + references/), not just a
   one-off doc, so the weekly content-generation routine (see
   `trend_predictor/docs/superpowers/specs/2026-08-17-social-media-automation-design.md`)
   can read and apply it without the founder re-explaining anything.
3. The founder's ongoing involvement should be limited to adjusting a small set of
   **config knobs** (cadence, tone/aggressiveness, content-type mix, etc.) — everything
   else (strategy execution, content decisions) should run автоматически.
4. **Explicitly NOT now**: analytics/performance-feedback loop (reading real post
   performance and learning from it). Founder said "not now" — don't build this yet,
   just note it as a clearly-scoped future phase so the strategy doc's design doesn't
   paint it into a corner.

## Where this lives

Recommended (stated to founder, not yet pushed back on): this new folder goes in
**`trend-signals-social`** (this repo), not `trend_predictor` — it's operational
marketing material the content-generation routine needs to read, not core IP.
Confirm this is still right before writing anything, in case the founder had a
different location in mind.

## Steps to execute (in order)

1. **Research** (3 parallel questions — prompts below are close to what was already
   dispatched and cancelled; reuse/adapt them):
   - **Algorithm mechanics 2026**: ranking signals by format (image/carousel/Reels),
     non-follower reach / interest-graph distribution triggers, new-account trust-ramp
     behavior, carousel-specific mechanics (slide count, completion rate, hook-slide
     weight), known suppression triggers to avoid, India-timezone posting-time data.
     Prioritize official Meta statements / Adam Mosseri interviews over SEO-blog
     speculation; flag evidenced vs speculative claims.
   - **Psychology of shareable/save-worthy content**: Jonah Berger's STEPPS framework
     applied to data/trend content specifically, curiosity-gap/hook psychology for
     "data reveal" posts, what makes something save-worthy vs just like-worthy,
     comment-bait mechanics — explicitly flagging which tactics conflict with this
     account's "receipts, not hype" credibility-first positioning.
   - **Documented fast-growth case studies**: real (cited) cases of accounts hitting
     tens of thousands to 500k+ followers fast, identifying the actual mechanism
     (viral snowball, serialized format, collab network, real-time trend-jacking,
     polarizing POV, proof/receipts format, etc.), explicitly calling out which cases
     relied on bought followers/engagement pods/follow-trains/bots (ToS-risk, avoid),
     and specifically looking for comparable niches (data-journalism, stats-reveal,
     finance-education, trend-spotting accounts) rather than meme/lifestyle pages.

2. **Synthesize into a skill folder** at `trend-signals-social/.claude/skills/instagram-growth/`:
   - `SKILL.md` — frontmatter (name, description) + the core actionable playbook:
     how to pick hooks, format carousels, choose posting times, decide content mix,
     when/how to trend-jack, what NOT to do (ToS-risk tactics, anything that undermines
     the "receipts not hype" brand). Written so a fresh session can follow it directly
     when generating weekly content.
   - `references/algorithm.md`, `references/psychology.md`, `references/case-studies.md`
     — the research findings, cited, kept separate from SKILL.md so the core skill
     stays short and the evidence is available on demand (matches how other skills in
     this environment structure references/ subfolders).
   - A config file (e.g. `config.yaml` or `CONFIG.md`) exposing the founder-tunable
     knobs — e.g. posting cadence, content-type ratio (signal/digest/build-in-public),
     tone aggressiveness, hashtag strategy on/off, trend-jacking on/off — clearly
     documented so the founder can edit values without needing to understand the full
     strategy doc.

3. **Explicitly stub, don't build, the analytics/learning loop** — add a short
   "Future work: performance feedback loop" section (in SKILL.md or a separate
   `FUTURE-analytics-loop.md`) describing the eventual shape (read Instagram Insights
   via the Graph API, feed post-performance back into content decisions) without
   implementing it. Keeps the door open without scope-creeping this pass.

4. Commit + push to `trend-signals-social`, update
   `trend_predictor`'s memory file `project-trendradar-social-automation.md` (via the
   auto-memory system) to note the skill now exists and where.

## Also still open (from before this ask, unrelated but worth remembering)

The weekly Claude-driven content-generation routine itself isn't wired up yet — right
now content was hand-generated once in a chat session to prove the publish pipeline
works (verified live, ig_post_id 17879480112511868). See
`trend_predictor` memory `project-trendradar-social-automation.md` for full state.
