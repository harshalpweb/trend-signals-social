# trend-signals-social

Automated Instagram publishing for `@trendradar.in`. This repo holds only
finished creative assets and the publishing pipeline — never the
`trend_predictor` engine, database, or entity map.

Full design: see `docs/superpowers/specs/2026-08-17-social-media-automation-design.md`
in the `trend_predictor` repo.

## How it works

1. **Content generation** (weekly, Claude-driven): a local Windows Scheduled
   Task (weekly, see "Scheduler" below — not a cloud agent) runs the
   `instagram-weekly-routine` skill in `.claude/skills/`, which reads current
   `trend_predictor` signals, generates that week's carousels via the Canva
   MCP tools (from the locked master template — see `instagram-carousel`),
   writes captions (`instagram-caption`), and pushes new entries into
   `content/queue/`. The whole strategy this runs on — algorithm mechanics,
   content psychology, case studies, visual design rules, and the
   founder-tunable config — lives in `instagram-growth`.
2. **Publishing** (`.github/workflows/publish.yml`, hourly): reads
   `content/queue/*.json`, publishes anything due via the Instagram Graph
   API, and moves it to `content/posted/` (or `content/failed/` after 3
   failed attempts).
3. **Token refresh** (`.github/workflows/refresh_token.yml`, monthly):
   renews the long-lived Instagram token before its ~60-day expiry.

## Instagram skills (`.claude/skills/`)

- `instagram-growth/` — the strategic playbook: research-backed rules (with
  sources, each tagged confirmed/speculative) on algorithm mechanics,
  shareable-content psychology, fast-growth case studies, and carousel
  design trends, plus `config.yaml` for the founder-tunable knobs (cadence,
  tone, content mix). Read this before touching strategy.
- `instagram-signals/` — pulls this week's top `trend_predictor` movers
  (read-only) and turns them into content angles.
- `instagram-caption/` — writes the caption + hashtags per post type.
- `instagram-carousel/` — generates on-brand slides from the locked Canva
  master template, self-critiques via `canva:get-design-feedback` and
  `canva:brand-check`, exports PNGs.
- `instagram-weekly-routine/` — the top-level orchestrator the scheduler
  actually invokes; runs the four skills above for the week and pushes the
  queue.

## Scheduler

A **local** Windows Scheduled Task (`TrendRadarWeeklyContent`, weekly Sunday
18:00 local time, registered by `trend_predictor/scripts/register_instagram_task.ps1`)
runs `instagram-weekly-routine` headlessly via `claude -p`. It's local rather
than a cloud routine because the account's Canva connection is a local
plugin and the routine needs the live local `trend_predictor` DB — see that
script's header comment for the full reasoning. This machine needs to be
powered on and logged in around the scheduled time for it to fire. Content
is queued ahead of each week automatically — no manual founder involvement
beyond optional spot-checking, and clearing `needs_review: true` flags (see
"Queue format" below) before those specific posts will go out.

## Queue format

See `content/queue/TEMPLATE.json`. One JSON file per post, plus its slide
PNGs under `content/queue/slides/`. `scheduled_time_ist` must include the
`+05:30` offset. To cancel a queued post before it goes out, delete its JSON
file (and slides) before `scheduled_time_ist`. `needs_review: true` means
`instagram-carousel`'s self-critique gate didn't fully pass after 2 revision
passes — `publish_due_posts.py` holds these and will **not** publish them on
schedule; edit the JSON and set `needs_review` to `false` once you've looked
at it to let it go out.

## Required GitHub Secrets

- `IG_ACCESS_TOKEN` — long-lived Instagram access token
- `IG_USER_ID` — Instagram Business Account ID (from `graph.instagram.com/me`)
- `REPO_ADMIN_TOKEN` — a **fine-grained PAT scoped to this repo only**, with
  "Secrets: Read and write" permission. Needed because the default
  `GITHUB_TOKEN` Actions provides cannot manage repo secrets — this is what
  lets `refresh_token.yml` write the renewed token back automatically. Create
  it at github.com → Settings → Developer settings → Fine-grained tokens →
  scope to this repo only, permission "Secrets" = Read and write.

## Manual test run

Both workflows support `workflow_dispatch`, so you can trigger a run by hand
from the repo's Actions tab instead of waiting for the schedule — useful for
the first end-to-end test once a real post is queued.
