# trend-signals-social

Automated Instagram publishing for `@trendradar.in`. This repo holds only
finished creative assets and the publishing pipeline — never the
`trend_predictor` engine, database, or entity map.

Full design: see `docs/superpowers/specs/2026-08-17-social-media-automation-design.md`
in the `trend_predictor` repo.

## How it works

1. **Content generation** (weekly, Claude-driven, not in this repo's code):
   a scheduled Claude Code routine reads current `trend_predictor` signals,
   generates that week's carousels via the Canva MCP tools, writes captions,
   and pushes new entries into `content/queue/`.
2. **Publishing** (`.github/workflows/publish.yml`, hourly): reads
   `content/queue/*.json`, publishes anything due via the Instagram Graph
   API, and moves it to `content/posted/` (or `content/failed/` after 3
   failed attempts).
3. **Token refresh** (`.github/workflows/refresh_token.yml`, monthly):
   renews the long-lived Instagram token before its ~60-day expiry.

## Queue format

See `content/queue/TEMPLATE.json`. One JSON file per post, plus its slide
PNGs under `content/queue/slides/`. `scheduled_time_ist` must include the
`+05:30` offset. To cancel a queued post before it goes out, delete its JSON
file (and slides) before `scheduled_time_ist`.

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
