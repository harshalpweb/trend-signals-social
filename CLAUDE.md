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
`quietly` banned outright. Run this mechanical check before shipping any
caption or locking in a voice exemplar:

```bash
py -3 -c "
import sys,re
t=open(sys.argv[1],encoding='utf-8').read(); w=len(t.split()); EM=chr(8212)
em=t.count(EM); rate=em/max(w,1)*100
print(f'words={w} em-dash={em} per100w={rate:.2f}  (cap 0.25, human 0.06-0.23)')
print('EM-DASH: ' + ('FAIL' if rate>0.25 else 'pass'))
for n,p in [('X-not-just-Y',r'(?i),\s+not\s+(just\s+)?[a-z]'),
            ('quietly',r'(?i)\bquietly\b'),('actually',r'(?i)\bactually\b')]:
    m=re.findall(p,t)
    if m: print(f'  {n}: {len(m)} hit(s)')
" <file>
```

A voice exemplar quoted inside any skill file must itself pass this check
before being locked in as "the voice to match" — an unaudited exemplar
propagates its own tells into everything written after it (this is
exactly what happened to `instagram-caption/SKILL.md`'s exemplar before
the 2026-08-25 fix). Full audit:
`income-engine/docs/consults/2026-08-25-cco-ai-tell-writing-audit.md`.
