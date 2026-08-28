---
name: instagram-weekly-routine
description: Top-level orchestrator for TrendRadar's Instagram content generation. Runs every 2 days (cadence changed from weekly 2026-08-28, founder decision) via a local Windows Scheduled Task (TrendRadarWeeklyContent — name kept for continuity, registered by scripts/register_instagram_task.ps1, whose Action invokes scripts/run_weekly_routine.py — not a cloud routine, see that script's header comment for why) and tops up the queue for the next 2 days, unattended. Use this skill directly when the routine fires; the sub-skills (instagram-signals, instagram-carousel, instagram-caption) are called from within it, not invoked separately in normal operation.
---

# Content-Generation Routine (every 2 days)

Fully automated. The founder's only recurring involvement is optional spot-checking of the queue before posts go live (or reviewing anything flagged `needs_review: true`) — never hands-on content creation.

**Horizon (changed 2026-08-28, founder cadence decision): each run covers
the NEXT 2 DAYS only** — today+1 and today+2 per `config.yaml`'s
`cadence.schedule` — not "the week ahead." This run is a *top-up check*,
not a quota: generate only the posts the schedule and the data honestly
support for those 2 days. A slot already covered by a surviving queue
entry is skipped, and a signal slot with no eligible entity ships as a
`no_signal` post (see `instagram-signals`), never as a stretched claim.

## Preconditions

- Read `instagram-growth/config.yaml` first — cadence, tone, and content-mix knobs live there and may have changed since this skill was last run.
- Confirm the `trend_predictor` repo checkout is reachable locally (see `instagram-signals` for path notes) and read-only access works.
- Confirm this run's horizon isn't already covered (check `content/queue/*.json` for entries dated inside the next 2 days before generating — prior runs' entries survive in the queue under this cadence, so a non-empty queue is normal, not an error).

## Steps, per `config.yaml`'s `cadence.schedule`

For each posting day in the next 2 days (currently Mon/Wed/Fri = signal, Sat = digest, Sun = build_in_public, Tue/Thu = no post — but read the actual config, don't hardcode this list):

1. **`instagram-signals`** — pull the content angle (skip for build_in_public).
2. **`instagram-caption`** — write the caption for that post type and angle.
3. **`instagram-carousel`** — generate, self-critique, and export the slide PNGs.
4. **Assemble the queue entry** — write one JSON file per post to `content/queue/` following `content/queue/TEMPLATE.json`'s schema exactly:
   - `id`: `{scheduled_date}-{type}-{NN}`
   - `scheduled_time_ist`: that day's date + `config.yaml`'s `posting_time_ist`, with the `+05:30` offset — do not omit the offset, the publish workflow depends on it.
   - `slides`: paths under `content/queue/slides/`, matching what `instagram-carousel` exported.
   - `status`: `"pending"`, `attempts`: `0`.
   - Add `"needs_review": true` if `instagram-carousel`'s self-critique gate didn't fully pass.
5. **Don't repeat a signal entity from the last 2 weeks** (see `instagram-signals`) — check ALL of: `content/posted/*/*.json` (nested one directory per post, not flat), **every surviving `content/queue/*.json` left by prior runs** (a still-pending post counts as featured — under every-2-days generation the queue is usually not empty), and this run's own new entries, before finalizing entity picks.

## After generating

1. `git add content/queue/` (new JSON + slide PNGs only — never touch `content/posted/`, `content/failed/`, or anything under `scripts/`).
2. `git pull --rebase origin main` **before** committing/pushing, then commit with a message like `content: queue {date range}` and push. The hourly `publish.yml` workflow also commits to `main` (moving posted files) — a plain push without rebasing first can get rejected by a commit it made in the meantime. If the push is still rejected after one rebase retry, pull-rebase again rather than force-pushing.
3. Everything after this is automatic — `.github/workflows/publish.yml` (hourly) picks up due posts from the queue, **except** any post queued with `needs_review: true`, which `publish_due_posts.py` holds until a human clears the flag. This skill does not publish anything itself.

## Failure handling

If any step fails for one post (e.g. `instagram-carousel` can't produce a passing design after retries), don't let it block the rest of the run — skip that post (log why), keep it out of the queue, and note it clearly in the commit message or a `content/queue/SKIPPED-{date}.md` note so the founder sees it on spot-check rather than silently losing a post.

## Scope

This skill does not touch `scripts/publish_due_posts.py`, `scripts/refresh_token.py`, or the GitHub Actions workflows — those are the separate, already-built publishing pipeline (pure Python, no AI, per the original design). This skill's job ends at `git push`.
