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
  **Narrow carve-out (founder ruling 2026-08-26, standing policy):**
  sessions may log into the Facebook account tied to this Page using the
  stored credentials (`docs/credentials/facebook.md`, gitignored) and
  handle any 2FA/OTP prompt that appears, specifically to manage this
  Facebook **Page's identity settings** — name, username/@handle, bio,
  profile/cover photo. Same scope shape as `digital_products`' Systeme.io
  carve-out (see that repo's `CLAUDE.md`). **Does NOT cover:** any
  payment-method/billing change, ad-account access, monetization-program
  enrollment, payout/bank/PAN/W-8BEN submission, deleting the account or
  Page, or anything on the founder's personal Facebook profile/other
  pages beyond this one. If ever unsure whether an action falls inside
  this carve-out, treat it as outside and ask — this is account access,
  not a reversible ₹0 item. Verify-before-done applies with extra
  weight: after any change, log out and independently re-fetch the live
  Page to confirm it actually persisted, same discipline the Systeme.io
  carve-out required after that page's own history of edits that looked
  successful but didn't land.

This repo lives as a sibling to `income-engine/` on disk
(`C:\Users\2026\Documents\trend-signals-social`), not nested inside it —
deliberate, not an oversight (see the registry entry's "Repo" line for
why moving it wasn't done as part of this absorption).

**Shared-checkout git safety (2026-08-25):** this is one physical directory
multiple concurrent Claude Code sessions commit into directly, not
per-session clones — discovered when a session's local commit sat unpushed
until another session found it by chance while pushing unrelated work.
`git_commit_guard.py` (wired above) only checks staged files at commit
time, not concurrent Edit/Write calls on the same file or another
session's unpushed local commits. Before any commit here — and especially
before merge/reset/rebase — run `git status` and `git log --oneline -5`
first, same discipline as `income-engine`'s own shared-repo git-safety
default.

## Customer-facing prose: human-voice rule (CCO audit, 2026-08-25)

Duplicated from `income-engine/CLAUDE.md` — this repo sits outside
`income-engine/` and does not inherit that file via Claude Code's
directory-hierarchy search, so this rule is repeated here verbatim.
Applies to every Instagram caption and any other customer/follower-facing
text this repo produces.

Measured against real human baselines (Paul Graham, Seth Godin, and a
topic-matched blog post; 0.06-0.23 em-dashes/100 words), every portfolio
artifact audited scored 8-74x that rate — this account's worst live post
scored 4.44/100w (19-74x). Standing rule: em-dash budget ≤1 per 400
words, never more than 1 per paragraph, **0 for a short social caption**;
avoid em-dash-introduced lists/parentheticals, "X, not (just) Y" tails,
"isn't X — it's Y" antitheses, balanced-antithesis semicolons, and
staccato-tricolon-plus-"Just X" resolutions; `actually` ≤1/500 words;
`quietly` banned outright.

**Mechanical check, 2026-08-26: use `copydesk`, not an inline script.**
The inline script this section used to carry only implemented a subset
of the rule above (missing the per-paragraph cap, caption mode, and the
isn't-X-it's-Y/semicolon-antithesis detectors) — exactly the kind of
drift the rule's own prose and its checker had fallen out of sync on.
`copydesk` (`income-engine/copydesk/`, a sibling subproject, own git
repo) is now the one canonical implementation; this repo doesn't
auto-inherit it any more than it auto-inherits `income-engine/CLAUDE.md`,
so call it by absolute path:

```bash
py -3 -m copydesk --caption <file>
```
(run from inside `C:\Users\2026\Documents\income-engine\copydesk`, or add
that directory to `PYTHONPATH` first — it isn't pip-installed). Drop
`--caption` for a longer piece where the general 1/400-words budget
applies instead of the short-caption 0-cap. Run this before shipping any
caption or locking in a voice exemplar — a voice exemplar quoted inside
any skill file must itself pass the check before being locked in as "the
voice to match," an unaudited exemplar propagates its own tells into
everything written after it (this is exactly what happened to
`instagram-caption/SKILL.md`'s exemplar before the 2026-08-25 fix). Full
audit: `income-engine/docs/consults/2026-08-25-cco-ai-tell-writing-audit.md`;
canonical rule source: `income-engine/copydesk/copydesk/rules.py`.
