---
name: instagram-weekly-routine
description: Top-level orchestrator for TrendRadar's weekly Instagram content generation. Runs once a week via a local Windows Scheduled Task (TrendRadarWeeklyContent, registered by trend_predictor/scripts/register_instagram_task.ps1 — not a cloud routine, see that script's header comment for why) and produces a full week of queued posts, unattended. Use this skill directly when the weekly routine fires; the sub-skills (instagram-signals, instagram-carousel, instagram-caption) are called from within it, not invoked separately in normal operation.
---

# Weekly Content-Generation Routine

Fully automated. The founder's only recurring involvement is optional spot-checking of the queue before posts go live (or reviewing anything flagged `needs_review: true`) — never hands-on content creation.

## Preconditions

- Read `instagram-growth/config.yaml` first — cadence, tone, and content-mix knobs live there and may have changed since this skill was last run.
- Confirm the `trend_predictor` repo checkout is reachable locally (see `instagram-signals` for path notes) and read-only access works.
- Confirm today's run hasn't already queued this week's posts (check `content/queue/*.json` for entries dated this week before generating duplicates).

## Steps, per `config.yaml`'s `cadence.schedule`

For each day in the week ahead (Mon/Wed/Fri = signal, Sat = digest, Sun = build_in_public, per current config — but read the actual config, don't hardcode this list):

1. **`instagram-signals`** — pull the content angle (skip for build_in_public).
2. **`instagram-caption`** — write the caption for that post type and angle.
3. **`instagram-carousel`** — generate, self-critique, and export the slide PNGs.
4. **Assemble the queue entry** — write one JSON file per post to `content/queue/` following `content/queue/TEMPLATE.json`'s schema exactly:
   - `id`: `{scheduled_date}-{type}-{NN}`
   - `scheduled_time_ist`: that day's date + `config.yaml`'s `posting_time_ist`, with the `+05:30` offset — do not omit the offset, the publish workflow depends on it.
   - `slides`: paths under `content/queue/slides/`, matching what `instagram-carousel` exported.
   - `status`: `"pending"`, `attempts`: `0`.
   - Add `"needs_review": true` if `instagram-carousel`'s self-critique gate didn't fully pass.
5. **Don't repeat a signal entity from the last 2 weeks** (see `instagram-signals`) — check `content/posted/*/*.json` (nested one directory per post, not flat) and this run's own new entries before finalizing the week's entity picks.

## After generating the week

1. `git add content/queue/` (new JSON + slide PNGs only — never touch `content/posted/`, `content/failed/`, or anything under `scripts/`).
2. `git pull --rebase origin main` **before** committing/pushing, then commit with a message like `content: queue week of {date}` and push. The hourly `publish.yml` workflow also commits to `main` (moving posted files) — a plain push without rebasing first can get rejected by a commit it made in the meantime. If the push is still rejected after one rebase retry, pull-rebase again rather than force-pushing.
3. Everything after this is automatic — `.github/workflows/publish.yml` (hourly) picks up due posts from the queue, **except** any post queued with `needs_review: true`, which `publish_due_posts.py` holds until a human clears the flag. This skill does not publish anything itself.

## Failure handling

If any step fails for one post (e.g. `instagram-carousel` can't produce a passing design after retries), don't let it block the rest of the week — skip that post (log why), keep it out of the queue, and note it clearly in the commit message or a `content/queue/SKIPPED-{date}.md` note so the founder sees it on spot-check rather than silently losing a post.

## Scope

This skill does not touch `scripts/publish_due_posts.py`, `scripts/refresh_token.py`, or the GitHub Actions workflows — those are the separate, already-built publishing pipeline (pure Python, no AI, per the original design). This skill's job ends at `git push`.
