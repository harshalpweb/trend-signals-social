# trend-signals-social

Automated Instagram publishing for `@trendradar.in`. This repo holds only
finished creative assets and the publishing pipeline — never the
`trend_predictor` engine, database, or entity map.

Full design: see `docs/superpowers/specs/2026-08-17-social-media-automation-design.md`
in the `trend_predictor` repo.

## How it works

1. **Content generation** (weekly, Claude-driven): a scheduled Claude Code
   cloud agent (weekly cron, see "Scheduler" below) runs the
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

A weekly cron-triggered cloud agent runs `instagram-weekly-routine` (see the
`schedule` skill in the Claude Code session that set this up). Content is
queued ahead of each week automatically — no manual founder involvement
beyond optional spot-checking.

## Queue format

See `content/queue/TEMPLATE.json`. One JSON file per post, plus its slide
PNGs under `content/queue/slides/`. `scheduled_time_ist` must include the
`+05:30` offset. To cancel a queued post before it goes out, delete its JSON
file (and slides) before `scheduled_time_ist`. `needs_review: true` means
`instagram-carousel`'s self-critique gate didn't fully pass after 2 revision
passes — worth a quick look before it publishes, though it'll still go out
on schedule if left untouched.

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
