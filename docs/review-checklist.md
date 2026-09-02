# TrendGiri content review checklist (standing, every batch, every lane)

Derived from the niche consult
(`income-engine/docs/consults/2026-08-29-group-cto-trendgiri-niche-and-content-strategy.md`
§2.7) and operationalized 2026-09-02 alongside the daily-build system.
Founder standing rule (2026-08-29): **no post reaches `content/queue/`
without a pass against this checklist, recorded per batch.** The checklist
is the portable form of the Fable review; an unattended run executes it as
its own mandatory final step, fail-closed: a post that can't clear it is
fixed or dropped (`SKIPPED-*.md` pattern), never queued as-is.

## Where the record lives

One file per daily batch: `content/reviews/YYYY-MM-DD-REVIEW.md`. For each
piece: PASS or FAIL per checklist item group, and for anything rejected,
what was rejected and why. A FAIL that gets fixed is re-checked and the
re-check noted. Weekly, Group CTO reviews the week's REVIEW trail plus live
permalinks in one sitting; findings amend this checklist.

## The checklist (per post)

### 1. Niche boundary
- [ ] "Would someone who sells online in India act differently because of
      this?" is a clear yes. Generic hustle motivation, generic startup
      news, and generic personal finance fail.

### 2. Lane rules
- [ ] The post follows its lane's rules (news: own-words + printed source
      name + date, primary sources first, quiet-week honesty; wisdom:
      original line, acts-on-it-tomorrow test, no hustle boilerplate;
      playbook: real worked numbers; signal/digest: freshness + freeze
      gates, no movement language on a bit-identical score; quote_card:
      no misattributed quotes ever; product_launch: at most 1 explicitly
      promotional post per week).

### 3. Hook
- [ ] Not a bare number; states a stake in seller language.
- [ ] Classified into one hook archetype (stake_statement, mid_story_open,
      contrarian_receipt, cost_of_ignoring, count_promise) and that
      classification is honest, not a label of convenience.

### 4. Anti-repetition (mechanical)
- [ ] `py -3 scripts/check_repetition.py check <candidate.json>` exited 0
      (or `append` did, at queue time). A gate failure is a real stop:
      change topic or angle, never relabel the candidate to sneak past.

### 5. Honesty
- [ ] Trend claims: freshness gate passed, no frozen-source movement
      language, source line present (generic form if Legal stripped the
      source name; never a stale "today" claim).
- [ ] News: every fact restated in our own words with outlet/primary
      source named and dated; a returning story is labeled as an update.
- [ ] Quotes: a named real person's quote has a primary-source-verified
      citation, or the line runs unattributed as ours.

### 6. Trend-jack (if any)
- [ ] The bridge to sellers fits in ONE clause. If it needs a second
      clause, the tie-in is forced: drop it.

### 7. Copy
- [ ] Caption AND every on-screen text line pass
      `py -3 -m copydesk --caption <file>` (run from
      `income-engine/copydesk`). Human-voice rule applies in full
      (repo `CLAUDE.md`).

### 8. Rotation
- [ ] Hook archetype differs from the previous post's; CTA type is not on
      a third consecutive day (both enforced by the gate; eyeball anyway).

### 9. Visual (carousel)
- [ ] `scripts/render_html/gate_check.py` all-PASS (tokens, contrast,
      ink coverage) AND every `_preview350/` image actually viewed at feed
      scale. The numbers do not replace eyes.

### 10. Visual + audio (Reel)
- [ ] Every rendered mp4 got a frame-level human/agent review (QA frames
      viewed, not just a passing ffmpeg exit).
- [ ] Hook frame: the first 1 second reads at thumbnail scale and states
      the stake.
- [ ] Audio: licensed track from `assets/audio/` (or newly licensed with
      the source logged in `assets/audio/ATTRIBUTION.md` at copy time);
      raw audio files never committed (public repo); mix audible, synced,
      not clipping.
- [ ] The day's two Reels do not share a visual device (gate-enforced) and
      do not look interchangeable at thumbnail scale (eyes).
- [ ] The daily quality-ratchet improvement is real: named in REVIEW.md
      and visible in the artifact, not just claimed.

### 11. Queue hygiene
- [ ] Queue JSON is `needs_review: true`, correct schema, correct slot; no
      edit to any queue file this run didn't create; the ledger row was
      appended via `check_repetition.py append`.
