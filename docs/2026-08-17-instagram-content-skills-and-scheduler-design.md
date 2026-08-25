# Instagram Content-Generation Skills & Scheduler — Design

Status: built 2026-08-17, autonomously (founder explicitly authorized proceeding without
per-step approval while away — "don't stop and get this all completed... I will just
review"). This doc is the paper trail; implementation lives in `trend-signals-social`
(separate public repo), except the scheduler registration script which lives here.

Extends `2026-08-17-social-media-automation-design.md` — builds the piece that doc left
as "not yet built": the weekly Claude-driven content-generation routine itself.

Moved here 2026-08-25 from `trend_predictor/docs/superpowers/specs/` as part of the
`instagram_sub_project` extraction (see `income-engine/docs/registry/instagram_sub_project.md`)
— this doc always described work that lives in this repo, it was just filed in the wrong
one during the original build session.

## What was decided (via brainstorming, before the founder stepped away)

- **Location**: skills live in `trend-signals-social/.claude/skills/`, not this repo —
  matches the existing repo split (this repo = engine/IP, that repo = everything
  Instagram-facing).
- **Skill breakdown**: `instagram-growth` (strategy/research), `instagram-signals`
  (pulls trend_predictor data), `instagram-caption`, `instagram-carousel` (Canva
  execution), `instagram-weekly-routine` (orchestrator) — approved as-is by the founder.
- **Quality bar**: locked brand template + brand kit, plus a self-critique gate
  (`canva:get-design-feedback` before queueing, up to 2 revision passes) — both
  approved.
- **Brand kit**: Canva's MCP tools have no API to create a formal Brand Kit
  (`list-brand-kits`/`search-brand-templates` both returned empty, and there is no
  create-brand-kit tool in the connected plugin). Worked around with a **master
  template design** (copied weekly via `copy-design`, not a real Brand Kit object) —
  same practical consistency, fully automatable, no manual Canva UI step needed. This
  is the same "find the automated way" pattern as the original design's storage
  workaround — see `[[feedback-find-the-free-automated-way]]` memory.
- **Logo**: judgement call delegated to Fable (founder: "ask fable or opus") while the
  founder was unreachable. Fable recommended a locked text wordmark over an AI-generated
  logo (avoids locking in mediocre AI-logo output across many posts; trivial to upgrade
  later). In practice, the account's first live post already established a
  globe-icon + "TrendRadar" wordmark lockup — the master template reuses that exact
  existing mark rather than introducing a new one, for consistency with what's already
  public.

## What was built

1. **Research** (4 parallel `haiku-researcher` agents): Instagram algorithm mechanics,
   shareable-content psychology, documented fast-growth case studies, and carousel
   visual-design trends — each claim tagged confirmed (Meta/Mosseri-official) or
   speculative (marketer consensus). Synthesized into
   `trend-signals-social/.claude/skills/instagram-growth/` (`SKILL.md` +
   `references/*.md` + `config.yaml` for founder-tunable knobs). This also completes
   the previously-cancelled `GROWTH-STRATEGY-TODO.md` task in that repo.
2. **Master Canva template**: design `DAHSjFtuvnU`, in a new `TrendRadar` Canva folder,
   matching the account's already-live visual identity (dark navy-teal, single teal
   accent, globe+wordmark, two-column footer). Documented with its element-ID map in
   `instagram-carousel/SKILL.md`.
3. **Four execution skills**: `instagram-signals` (documents the actual
   `trendpredictor.store.Store.read_latest_scores` / `festival.upcoming` calls to use —
   verify these still exist before relying on them, the engine evolves),
   `instagram-caption`, `instagram-carousel`, `instagram-weekly-routine`.
4. **Scheduler — local, not cloud** (a mid-build correction — see below):
   `scripts/register_instagram_task.ps1` (this repo) registers a Windows Scheduled Task,
   `TrendRadarWeeklyContent`, weekly Sunday 18:00 local time, running `claude -p`
   headlessly against the `trend-signals-social` checkout with a scoped
   `--allowed-tools` list and `--permission-mode acceptEdits`. Mirrors the existing
   `TrendPredictorDaily` / `TrendPredictorBackup` task pattern in
   `scripts/register_task.ps1`.

## Why the scheduler is a local Task, not a cloud routine

The original design doc assumed a "cron-triggered cloud agent." When actually building
it, the `schedule` skill's cloud-routine mechanism (`RemoteTrigger`) turned out to only
support Gmail/Todoist/Calendar/Drive as attachable MCP connectors — **not Canva** —
and cloud routines only see whatever's committed to git, not this machine's live
`data/trend.db`. Both are hard requirements for this pipeline. A local Windows
Scheduled Task running the Claude Code CLI headlessly has full access to both the local
Canva plugin connection and the live DB, so that's what was built instead. If Canva
becomes available as a cloud connector later, this could move to a cloud routine — not
worth doing until then.

## Fix round (opus-reviewer, same session)

A verified review — the reviewer actually ran the skills' documented code against the
live `trend.db` rather than reading only — caught several bugs before this shipped as
"done":

- **False-corroboration risk (the one that mattered most)**: `detail.agreeing` (which
  signal families corroborate an entity) is nested inside a JSON-string `detail` field,
  not a top-level row key as first documented, and nearly every entity in the live DB
  currently has exactly one agreeing family. The original caption instruction ("state
  which signals agree") would have published a false multi-source-corroboration claim —
  exactly the kind of thing this "receipts, not hype" brand can't survive. Fixed: both
  `instagram-signals` and `instagram-caption` now gate corroboration language on an
  actual count ≥ 2, falling back to honest single-source framing otherwise.
- Wrong Python interpreter documented (venv lacks the package; `py -3.12` works —
  verified live), a snippet that crashes on rows without a `composite` key, and a
  dedupe glob that didn't match the actual nested `content/posted/{id}/{id}.json` layout.
- `needs_review` was documented as a spot-check flag but `publish_due_posts.py` never
  read it — fixed so flagged posts are held, not shipped on schedule.
- Weekly push could race the hourly publish workflow's own commits — added
  `pull --rebase` before push.
- `register_instagram_task.ps1` was missing `--add-dir` for the trend_predictor
  checkout (instagram-signals reads outside the task's working directory) and its
  Canva allowed-tools list was missing several tools the `canva:get-design-feedback`/
  `canva:brand-check` plugin skills call internally — switched to allowing the whole
  Canva plugin MCP server via wildcard (`mcp__plugin_canva_canva__*` — confirmed via
  Claude Code's own docs that this is the correct allow-rule syntax; the bare server
  name without `__*` only works for deny/ask rules, not allow) instead of an enumerable
  list that would go stale. **Verified fixed** with a live headless smoke test
  (`claude -p` from `trend-signals-social` with `--add-dir` to trend_predictor, no
  Canva calls) — read both changed skill files, confirmed cross-repo file access, and
  confirmed the corrected Python import path all worked with no permission-prompt hang.
  (The reviewer's claim that the directory would hit an un-trusted-workspace dialog on
  first headless run did not reproduce — the CLI's own `--help` text says the trust
  dialog is skipped in non-interactive/`-p` mode, and the smoke test confirms it.)
- Docs (README, skill descriptions) still described the abandoned cloud-agent scheduler
  after it was corrected to a local Task mid-build — fixed for consistency.
- A fabricated "93%" source-citation stat and an inconsistent engagement-rate range
  that silently merged two different studies into one number — both removed/corrected.

All fixes committed and pushed to `trend-signals-social` (`ac96e82`) and to
`register_instagram_task.ps1` here.

## Open items for founder review

- The Canva Brand Kit workaround (master template + `copy-design`) hasn't run through a
  real weekly cycle yet — first live automated run happens the next scheduled Sunday
  18:00, or can be triggered manually before then to verify end-to-end.
- `register_instagram_task.ps1`'s `--allowed-tools` list is scoped to what the skills
  describe needing; if a future edit to the skills adds a new Canva MCP call or other
  tool, this script needs a matching update and re-run, or the unattended run will hang
  on an unanswered permission prompt.
- Analytics/performance-feedback loop remains explicitly not built, per the founder's
  earlier "not now."

## Update, 2026-08-25 (trendradar diagnosis, folded in during extraction)

The weekly Task runs and reports success (`LastTaskResult: 0`) every week, but every
Canva MCP call has actually been getting denied since the start — the runtime call goes
through `mcp__claude_ai_Canva__*`, not the `mcp__plugin_canva_canva__*` allowed above.
The process correctly refuses to fake output and exits 0, which is why Task Scheduler
shows clean success while nothing gets built/committed/published. A one-line fix was
diagnosed and verified but not yet applied — blocked by the auto-mode safety classifier
on `Set-ScheduledTask` (a system-level change), correctly not routed around. See
`income-engine/docs/registry/instagram_sub_project.md` for current status.
