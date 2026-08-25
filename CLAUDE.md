# trend-signals-social (instagram_sub_project) — standing instructions

Minimal charter per `register-a-subproject` skill's step 2, carrying the
portfolio's three cross-subproject execution standards until this
subproject needs a fuller one of its own. This repo is the real,
already-live implementation absorbed from `trendradar`'s registration on
2026-08-25 — see `income-engine/docs/registry/instagram_sub_project.md`
for current status (authoritative for cross-portfolio visibility).

- Implementer → reviewer ladder for anything beyond routine content ops.
- Fix-round circuit breaker: rounds 1-3 same implementer; round ≥4
  escalates one model tier; round 5 is a hard stop — adjudicate and
  report BLOCKED, never open round 6.
- 2-3 concurrent-dispatch cap, write-ahead dispatch ledger for anything
  beyond one or two agents in flight.
- Founder-reserved items (per `income-engine/CLAUDE.md`, unchanged here):
  real-money spend, account auth (Meta Business Suite login/OTP,
  monetization-program enrollment, payout/bank/PAN/W-8BEN submission),
  `Set-ScheduledTask` / other system-level scheduled-task edits, public
  or irreversible acts under the founder's identity (this repo publishes
  live to `@trendradar.in` via its own hourly GitHub Actions workflow —
  treat anything that touches publish timing/content-approval logic with
  that in mind).

This repo lives as a sibling to `income-engine/` on disk
(`C:\Users\2026\Documents\trend-signals-social`), not nested inside it —
deliberate, not an oversight (see the registry entry's "Repo" line for
why moving it wasn't done as part of this absorption).
