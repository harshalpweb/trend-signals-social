# Platform inventory

Owner: **Chief Social Media Manager (CSMM)**. One row per platform we hold or operate.
Update this file whenever an account, app, auth model, token, rail or status changes.

Control-plane design: `trend_predictor/docs/superpowers/specs/2026-08-19-meta-control-plane-adr.md`.
Secrets live in user-level Windows env vars and GitHub Actions secrets only — never in this file.

Last verified: **2026-08-19** (CSMM live probe).

## Meta

| Field | Value |
|---|---|
| Platform | Instagram (Meta) |
| Account | **@trendradar.in** |
| IG user id | `27870001472663258` |
| App / auth model | Meta app using **"Instagram API with Instagram Login"** — tokens are `IGAA…` and are valid **only** on `graph.instagram.com`, not `graph.facebook.com` |
| API version | **v21.0**, pinned in ONE place: `GRAPH_API_VERSION` in `scripts/ig_common.py` (overridable per-run with the `GRAPH_API_VERSION` env var). v21.0 sunsets **~Oct 2026** — the bump is a one-constant change, then re-run the test suite. |
| Auth switch | `IG_AUTH_MODE` env var / repo variable: `instagram_login` (**default, live today**) → `https://graph.instagram.com`; `facebook_login` → `https://graph.facebook.com`. Unset/empty = default, so absent config behaves exactly as before. |
| Scopes | `instagram_business_basic`, `instagram_business_content_publish` (Instagram-Login use case) |
| Token | long-lived, ~60 days; auto-refreshed **monthly** by `.github/workflows/refresh_token.yml` → `scripts/refresh_token.py` (writes the new value back into the `IG_ACCESS_TOKEN` repo secret) |
| Secret locations | GitHub Actions secrets `IG_ACCESS_TOKEN`, `IG_USER_ID`, `REPO_ADMIN_TOKEN`; local user env vars `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_USER_ID` (`HKCU\Environment`) |
| Rails | `.github/workflows/publish.yml` — **hourly** (`cron: 0 * * * *`), runs `scripts/check_token.py` then `scripts/publish_due_posts.py` over the JSON queue in `content/queue/` |
| Health probe | `py -3.12 scripts/check_token.py` (exit 0 live / 2 OAuthException / 3 config / 4 network). CI adds `--incident-file content/INCIDENT.json --due-count "$DUE"` — see "Incident throttle" below. |
| Graph client | `scripts/ig_common.py` — all three scripts go through it: token in an `Authorization: Bearer` header (never a query string), 30s timeout, every error string redacted. Tests: `py -3.12 -m pytest -q` (offline). |
| Publishing cap | ~25 API posts per rolling 24h — `GET /{ig-user-id}/content_publishing_limit` before any batch |
| Status | 🟢 **RESOLVED 2026-08-19** — root cause was a **developer-account confirmation checkpoint** (Meta "unusual activity"), not the app. Founder completed the identity checkpoint; token probe flipped to `OK: token live for @trendradar.in`. Incident file auto-clears (`RECOVERED`) on the next hourly run. |
| App ID | **2230374924469484** (TrendRadar Publisher), mode dev / unpublished, compliance `compliant`, no open violations (read via `meta-devtools` after re-consent). |
| IG business-account id | **17841440746293693** (the `/me` `user_id` on graph.instagram.com). NOTE: `27870001472663258` is the **app-scoped** id (`/me` `id`), NOT the Graph business-account id — conflating them caused failed calls on 2026-08-19. |
| Facebook Page | **TrendRadar** — Graph page id **`1207351012469462`** (via meta-ads `ads_get_user_pages`); `61593158354383` is the *profile* id (new-Pages-experience), not a Graph object. Linked to @trendradar.in (IG messages-in-Inbox on). **Page API control deferred** — see below. |
| Control plane | **Instagram runs on graph.instagram.com** via `scripts/ig_common.py` + the existing IG-Login token — publish, comments, insights, DMs all supported there. The OSS meta-mcp (graph.facebook.com) was **dropped** (CTO 2026-08-19): our app is Facebook-Login-for-Business, which needs a business login *configuration* to grant page/IG assets, not raw scopes. FB Page / Ads / Threads **deferred** until the CRO ledger justifies them (Ads = CFO-gated real money). |

### Incident detail — code 200 (opened 2026-08-19)

Reproduced 2026-08-19 by CSMM against `graph.instagram.com/v21.0` with the current
181-character `IGAA…` long-lived token read from `HKCU\Environment`:

| Endpoint | Result |
|---|---|
| `GET /me?fields=id,username` | HTTP 400 — `{"error":{"message":"API access blocked.","type":"OAuthException","code":200,...}}` |
| `GET /me/content_publishing_limit` | HTTP 400 — same error, `code 200` |

**Diagnosis:** code 200 is an **app/account-level restriction**, not token expiry (expiry is
code 190). The token parses and is well-formed; the app is blocked. Usual causes, in the order
to check them: Data Use Checkup overdue → business verification incomplete → app still in
dev mode with a missing role → a policy action. Refreshing the token will **not** clear it.

~~**Blocked on:** founder OAuth for the `meta-devtools` MCP.~~ **RESOLVED 2026-08-19.**
Real root cause: a **developer-account confirmation checkpoint** on the "Trend Radar" account
(`developers.facebook.com/apps/` showed "Account confirmation needed — unusual activity"; the app
itself was fine). This is why every Graph call returned code 200 and why the devtools grant first
showed zero apps. The founder completed the identity checkpoint (email confirmation code — an
account-auth step only they can do); immediately after, `check_token.py` returned exit 0
`OK: token live`, `meta-devtools devtools_app_list` returned the app with read+manage, and
`devtools_compliance` returned `overall_status: compliant`, no open violations. No appeal needed.
The Facebook Page was then created and linked to @trendradar.in (see status table).

**Impact:** no post has actually exercised the token since 2026-08-17 — every hourly run since
has printed "No due posts", so the restriction has been invisible. The next genuinely due post
would have failed silently on a green run before today's `publish.yml` change.

**Confirmed in production 2026-08-18T21:03Z** — GitHub Actions run
[`32185651913`](https://github.com/harshalpweb/trend-signals-social/actions/runs/32185651913),
*Publish due posts* → *Check Instagram token health*, **red**:

```
FAIL: OAuthException code=200: API access blocked.
```

So the restriction is on the **app/account**, not on this machine, this token copy, or the local
environment: CI holds a separately-stored copy of the same long-lived token, resolves DNS from a
GitHub runner, and gets the identical error. That closes off "stale local env var" and "corrupted
token string" as explanations. The health gate itself is therefore proven end-to-end — it caught a
real, live failure on its first production run.

### Incident throttle (added 2026-08-19)

The gate working correctly created a second problem: an hourly cron that goes red every hour for
one known, **founder-blocked** cause emails the founder ~24×/day and trains everyone to ignore the
alert — at which point the gate is worse than useless. `check_token.py` now takes
`--incident-file PATH` and `--due-count N`, and `publish.yml` computes
`DUE=$(python scripts/publish_due_posts.py --count-due)` first:

| Situation | Exit | Run | Why |
|---|---|---|---|
| First detection (no `content/INCIDENT.json`) | 2 | 🔴 red | One notification per incident — the founder must learn about it. |
| Repeat detection, `DUE=0` | 0 | 🟢 green + `WARN:` line | Nothing was lost this hour; there is no new information to send. |
| Repeat detection, `DUE>0` | 2 | 🔴 red | Posts are due and cannot go out — new damage every hour, so alert every hour. |
| Corrupt/unreadable incident file | 2 | 🔴 red | A mangled file must never be able to silence an alert. |
| `$DUE` empty or non-numeric | 2 | 🔴 red | "Unknown" is treated as "posts are due" — fail loudly rather than risk silent loss. |
| Token live again, incident file present | 0 | 🟢 green + `RECOVERED:` line | See below. |

Not throttled on purpose: exit 3 (missing config) and exit 4 (network/parse). Those are a broken
setup or a self-clearing transient, not a standing incident.

`content/INCIDENT.json` is the durable record, committed by the workflow's `git add -A content/`
step (which also stages its deletion on recovery):

```json
{
  "first_seen_utc": "...", "last_seen_utc": "...", "checks_failed": 7,
  "code": 200, "message": "OAuthException code=200: API access blocked.",
  "auth_mode": "instagram_login", "hint": "code 200 is an app/account-level restriction, ..."
}
```

`message` and `hint` go through `redact()` before they are written — this file is committed to the
repo, so it is under exactly the same no-secret rule as `post["last_error"]`.

**Nothing is hidden while quiet:** a throttled hour still prints the full `FAIL:` + `HINT:` lines
and still increments `checks_failed`, so `git log content/INCIDENT.json` reconstructs the whole
outage. And a throttled hour cannot burn API attempts: with `DUE=0` the publish step runs but
`load_due_posts()` returns nothing and makes zero Graph calls; with `DUE>0` the check exits 2 and
the publish step is skipped entirely.

**Recovery signal — how you know it is over.** Two things happen together on the first green probe:

```
OK: token live for @trendradar.in (id=…)
RECOVERED: token live again - incident open since <first_seen> (<n> failed checks) cleared; removed content/INCIDENT.json
```

and `content/INCIDENT.json` **disappears from the repo** in that run's `chore: publish run …`
commit. Either signal alone is enough; the file's absence is the one to check when reading state
rather than logs. When it clears, update the Status row above and close this section.

**Watch item:** the throttle buys quiet only until the next queued post comes due. `content/queue/`
currently holds pending posts for 2026-08-19/21/22/23 — from the moment one of them is due, `DUE>0`
and the hourly run is red again every hour, by design (posts really are being lost). If the incident
is still open then, the queue should be pushed out or held (`needs_review: true`) rather than the
alert weakened — that is a Growth-Lead/CoS queue decision, not a CSMM one.

## Incident root cause — 2026-08-19

Investigated by CSMM after the founder completed OAuth for the official `meta-devtools` and
`meta-ads` MCPs. **Outcome: root cause narrowed but NOT confirmed — the diagnostic path is itself
blocked.** Facts below; no token, app secret or app id is recorded here.

### What was re-confirmed (live, this session)

Direct read-only probes against `graph.instagram.com/v21.0`, token read from `HKCU\Environment`
(181 chars, `IGAA…`), `Authorization: Bearer` header, all output redacted:

| Endpoint | Result |
|---|---|
| `GET /me?fields=id,username` | HTTP 400 — `API access blocked.` / `OAuthException` / **code 200** |
| `GET /debug_token` | HTTP 400 — same, code 200 |
| `GET /{ig-user-id}/content_publishing_limit` | HTTP 400 — same, code 200 |

The block is **app-wide** (it also hits `/debug_token`, an app-scoped endpoint), server-side, and
reproduces from this machine and from a GitHub runner. Token expiry (code 190) and local
environment are excluded.

### What Meta's own docs say about code 200

- Graph-wide error table (WhatsApp support → *Authorization errors*): **`200-299 API Permission —
  "Permission is either not granted or has been removed."`** (HTTP 403 class).
- Messenger error table: `200 Permission Error` — permission not reviewed / **app not live**.
- The **Instagram Platform error-code table has no code-200 entry at all.** Notably, an
  Instagram *account* restriction is a **different** error — `code 25 / subcode 2207050`
  ("The Instagram account is restricted… inactive, checkpointed, or restricted"). We are not
  seeing that, which argues against a plain IG-account checkpoint.
- Related IG code `2534041`: *"The owner of the Instagram Professional account has revoked your
  app's access."* — the revocation family is a live hypothesis.

**Reading:** code 200 = an app permission that was **never granted or has been removed**. Consistent
with (a) the app being deactivated/restricted so its permissions lapsed, or (b) the Instagram user
having revoked the app. Not yet distinguishable with the tools available.

### Why the MCP diagnosis could not be completed

`mcp__meta-devtools__devtools_app_list` (action `list`, retried with `limit: 100`) returns:

```json
{"data":{"apps":[],"pagination":{"has_next_page":false}},"meta":{"auth_type":"USER_ACCESS_TOKEN"}}
```

**Zero apps.** Authentication itself succeeded (`auth_type: USER_ACCESS_TOKEN`, well-formed
responses, no auth error). Per the tool's own contract, apps that are **restricted or deactivated
are still listed**, carrying a `status` object — so an empty list does **not** mean "the app is
restricted". It means the OAuth grant covers no apps. Causes, in likelihood order:

1. The app was **not selected on the DevTools consent screen** (the grant is per-app, opt-in).
2. The founder authorised with a **Facebook account that holds no role** on the app.
3. The app has been **deleted**.

Every other devtools tool — `devtools_app` (settings/mode/products), `devtools_app_review`,
`devtools_compliance` (Data Use Checkup, verification, violations), `devtools_api_usage`
(rate limits), `devtools_webhook_list` — **requires an `app_id`**. With no app listed and no app id
recorded anywhere (searched `docs/`, `scripts/`, git history via `git log -S`, `~/.claude.json`;
`META_APP_ID`/`META_APP_SECRET` are unset in `HKCU\Environment`), none of them could be called.
App mode, products, permissions, roles, App Review status, compliance findings, rate limits and
webhook subscriptions therefore remain **unread**.

### Meta Ads (read-only)

`mcp__meta-ads__ads_get_ad_accounts` → `{"ad_accounts": []}`. No ad account and no owning business
is visible. This matches the intended state (no ad account, no payment method), but note it is
**not distinguishable** from the same "granted no assets" condition seen in devtools. No write
calls were made.

### Remediation facts (from Meta docs, for sequencing)

- Data Use Checkup is **not required while an app is in Development mode**, and **not required for
  Standard Access**. If this app is dev-mode/standard-access, DUC is an unlikely cause.
- If DUC *is* overdue: *"your app will be deactivated until DUC is completed."*
- Reactivating an inactive app is expensive: *"any app that becomes inactive must have their use
  cases, permissions and features **re-approved through App Review**"*, plus DUC.
- Tech-Provider **Access Verification** failures return **code 100**, not 200, and only apply when
  an app is used by *other* businesses — ruled out here.

### Consequence for Path 1

Path 1 (link a Facebook Page + move to Facebook Login for Business) should **not** be executed
blind on this app. The choice depends on one unread fact:

- App shows **healthy** → run Path 1 on this app (runbook above unchanged).
- App shows **deactivated / restricted** → Path 1 on it inherits App Review + DUC. A **fresh app**
  is likely cheaper: own-account IG publishing via Facebook Login for Business needs
  `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, which
  work at Standard Access for assets the app admin owns.
- Restriction sits on the **developer account or business** → a fresh app fails identically. The
  dashboard alert surface is where this is visible.

**Status: still 🔴 open.** Blocked on one founder dashboard action (below), not on engineering.

### Founder action required — re-consent DevTools with the app selected

Everything downstream is gated on one browser step. Nothing here needs a token pasted anywhere,
and nothing here is irreversible.

**Step 1 — put the app in the DevTools grant (2 minutes).**

```
claude mcp login meta-devtools
```

On the consent screen there is a **per-app picker**. The current grant has **zero** apps ticked,
which is why every app-scoped tool is dead. Tick the @trendradar.in Instagram app (and any other
app we own) and approve. If the app does not appear in the picker at all, that is itself the
answer — jump to Step 2b.

**Step 2 — while in the browser, read the two dashboard surfaces we cannot reach.**

Go to <https://developers.facebook.com/apps> and open the app:

- **2a.** Note the **App ID** (this is a public identifier — safe to paste back in chat) and any
  red banner / **Alerts inbox** entry. The specific things worth reading out: app **mode**
  (Development vs Live), whether **Data Use Checkup** is flagged overdue, and whether App Review →
  *Permissions and Features* still shows `instagram_business_basic` /
  `instagram_business_content_publish` as granted.
- **2b.** If the app is **missing from `developers.facebook.com/apps` entirely**, the cause is not
  a consent-picker miss — it is a removed role or a deleted app, and the recovery is a fresh app
  rather than a repair. Say so and we re-plan.

**Do NOT do yet:** the Path 1 switch-over (Facebook Page link, "Facebook Login for Business"
product, 9-scope token). Reasons under "Consequence for Path 1" above — in short, if the app is
deactivated, those permissions are **not grantable** until DUC + App Review are cleared, so
generating the token would fail and the session would be wasted. Sequence is: read status →
then choose repair-this-app vs fresh-app → then Path 1.

**Timing — how much runway is left.** Measured 2026-08-19 04:44 UTC:

| Fact | Value |
|---|---|
| `python scripts/publish_due_posts.py --count-due` | `0` |
| Next queued post | `2026-08-19-signal-01` @ `2026-08-19T20:00+05:30` = **14:30 UTC** |
| Runway before it is due | **~9h 45m** |
| `content/INCIDENT.json` | open, `checks_failed: 8`, `last_seen_utc 2026-08-19T04:42:12Z` |

Until 14:30 UTC the hourly run stays **green** (throttled, `DUE=0`) and nothing is being lost.
From 14:30 UTC the run goes **red every hour** and posts are genuinely missed — by design. If the
incident is still open by then, the correct move is to push the queue dates out or set
`needs_review: true` (a Growth-Lead/CoS call), **not** to weaken the alert.

## Shared Graph client — `scripts/ig_common.py`

Every rail (`check_token.py`, `publish_due_posts.py`, `refresh_token.py`) calls Meta only
through this module. It exists for two reasons:

**1. Secret containment.** `requests` embeds the full request URL — query string included — in
`HTTPError`/`RequestException` messages. The old code passed `access_token=` as a query param,
so an ordinary 400 during a publish put the live token into `post["last_error"]`, which
`publish.yml`'s `if: always()` step then **committed to this repo**. Now: the token travels in an
`Authorization: Bearer` header, and every string that leaves the process passes through
`redact()`, which substitutes `<REDACTED>` for each registered secret (access token, GitHub admin
PAT, `META_APP_SECRET`). Regression-tested in `tests/test_ig_common.py`
(`test_forced_failure_exits_one_and_last_error_has_no_token`).

One deliberate exception: the `facebook_login` refresh flow is `fb_exchange_token`, which Meta
only accepts as a query parameter. Redaction is therefore load-bearing there, not belt-and-braces.

**2. Host switching.** `IG_AUTH_MODE` selects host *and* refresh flow:

| `IG_AUTH_MODE` | host | refresh call |
|---|---|---|
| `instagram_login` (default) | `graph.instagram.com` | `GET /refresh_access_token?grant_type=ig_refresh_token` |
| `facebook_login` | `graph.facebook.com` | `GET /{version}/oauth/access_token?grant_type=fb_exchange_token&client_id=$META_APP_ID&client_secret=$META_APP_SECRET` |

Header auth falls back once to query-param auth if Meta answers an auth-shaped `code 190`
(`graph.instagram.com` historically only documented the param form). An auth failure means nothing
was performed server-side, so the retry cannot double-post.

## Path 1 switch-over runbook

Run this **after** the founder has, in a browser: linked a Facebook Page to @trendradar.in,
switched the Meta app to the *Facebook Login for Business* Instagram flow, granted
`instagram_basic` + `instagram_content_publish` + `pages_show_list` + `pages_read_engagement`,
and produced a long-lived Page/User token (`EAA…`). Everything below is CoS-executable in minutes.

**Values the founder must hand over (never written to this file or any tracked file):**
`META_APP_ID`, `META_APP_SECRET`, the new long-lived `EAA…` token, and the IG-Business-Account id
returned by `GET /me/accounts?fields=instagram_business_account` (it is a *different* id from the
Instagram-Login one currently recorded above).

1. **Local (Windows user env vars), for interactive MCP/CLI use:**
   ```
   setx IG_AUTH_MODE facebook_login
   setx IG_ACCESS_TOKEN "<EAA… token>"
   setx IG_USER_ID "<ig-business-account-id>"
   setx META_APP_ID "<app id>"
   setx META_APP_SECRET "<app secret>"
   ```
   Also set `INSTAGRAM_ACCESS_TOKEN` / `INSTAGRAM_USER_ID` to the same two values — the OSS
   `meta` MCP reads those names, the repo scripts read `IG_*`.
   `setx` does **not** reach already-running processes — open a **new** terminal (and restart
   Claude Code) before verifying, or you will get a misleading `code 190 "Cannot parse access
   token"` from the literal placeholder.

2. **Verify locally, read-only, before touching CI:**
   ```
   py -3.12 scripts/check_token.py
   ```
   Expected on success:
   ```
   Probing https://graph.facebook.com/v21.0/me (IG_AUTH_MODE=facebook_login)
   OK: token live for @trendradar.in (id=<ig-business-account-id>)
   ```
   Exit codes: `0` live · `2` OAuthException (`190` = bad/expired token → re-auth; `200` = app or
   account restriction → Meta Developer Tools compliance findings, *not* a token problem) ·
   `3` config (missing env var or bad `IG_AUTH_MODE`) · `4` network. A `WARN: IG_USER_ID env … !=
   id returned by /me` line means step 1 used the old Instagram-Login id — fix it before publishing.

3. **GitHub (repo settings → Secrets and variables → Actions):**
   - Repository **variable** `IG_AUTH_MODE` = `facebook_login`
   - Repository **secrets**: update `IG_ACCESS_TOKEN`, update `IG_USER_ID`,
     add `META_APP_ID`, add `META_APP_SECRET`
   - `REPO_ADMIN_TOKEN` is unchanged.
   Both workflows already read these with safe defaults, so nothing else needs editing.

4. **Prove it in CI without publishing:** run the *Refresh Instagram token* workflow via
   `workflow_dispatch`. It exercises `facebook_login` refresh + the secret write-back, and
   publishes nothing. Then check the *Publish due posts* workflow's "Check Instagram token
   health" step on its next hourly run (or dispatch it while the queue has no due post).

5. **Update this file:** IG user id, auth model, scopes, token type (`EAA…`), status; and record
   the Facebook Page under "Other Meta surfaces".

**Rollback:** set the repo variable `IG_AUTH_MODE` back to `instagram_login` and restore the
previous `IG_ACCESS_TOKEN`/`IG_USER_ID` secret values. No code change is involved either way.

**Unlocked by Path 1:** the OSS `meta` MCP works unchanged (it hardcodes
`graph.facebook.com/v26.0`), plus Facebook Page publishing, richer IG endpoints, and Ads
eligibility.

## Other Meta surfaces

| Surface | State (2026-08-19) |
|---|---|
| Threads | account not yet authorised; `THREADS_ACCESS_TOKEN` / `THREADS_USER_ID` unset. Threads API is independent of the IG auth gap, so it can go live before Path 1 lands. |
| Facebook Page | none linked yet — this is the Path 1 prerequisite |
| Meta Ads | `meta-ads` MCP registered at user scope; founder OAuth **done 2026-08-19** and calls authenticate. `ads_get_ad_accounts` → `[]` — no ad account, no payment method (deliberate: spend stays impossible until the founder unlocks it). Note the empty list is **not** proof of "no ad account exists" — it is indistinguishable from the same zero-asset grant seen in devtools. |
| Webhooks | none subscribed |

## MCP control surfaces

| Server | Scope | Tools | Auth state |
|---|---|---|---|
| `meta` (OSS `@mikusnuz/meta-mcp` v2.1.x, MIT) | inline in `.claude/agents/chief-social-media-manager.md` | 66 (33 IG, 27 Threads, 6 app/token/webhook) | env-var driven; **currently broken — see defect below** |
| `meta-devtools` (official) | user (`~/.claude.json`) | app settings, compliance findings, App Review, rate limits, webhooks | ⚠️ OAuth **done** 2026-08-19 and calls authenticate, but the grant covers **0 apps** — every app-scoped tool is unusable. Needs re-consent with the app selected. |
| `meta-ads` (official) | user (`~/.claude.json`) | ~29 ads tools | ⚠️ OAuth **done** 2026-08-19; `ads_get_ad_accounts` → `[]` (no ad account visible) |

**Open defect (found 2026-08-19, re-tested after restart — original fix was WRONG):**

Originally diagnosed as stale `setx` env vars in a long-running process, with "restart Claude
Code" as the fix. **Re-tested 2026-08-19 in a post-restart session — still broken, and the error
changed, which is the informative part:**

| When | Call | Error |
|---|---|---|
| Before restart | `mcp__meta__ig_get_profile` | code 190 **"Cannot parse access token"**, path literally `/${INSTAGRAM_USER_ID}` |
| After restart | `mcp__meta__meta_get_app_info` | code 190 **"Error validating application. Invalid application ID."** |

A *different* error proves the restart worked and placeholder expansion is no longer the issue.
The remaining cause is simpler: **`META_APP_ID` and `META_APP_SECRET` were never set at all** —
both are absent from `HKCU\Environment` and from every `.env` on this machine. So the OSS `meta`
server has no app identity to authenticate with.

**Real fix (blocked on the founder action above):** obtain the App ID + App Secret from the app
dashboard, then set `META_APP_ID` / `META_APP_SECRET` (plus `INSTAGRAM_ACCESS_TOKEN` /
`INSTAGRAM_USER_ID`) as user env vars and start a fresh session. Re-verify with
`mcp__meta__ig_get_profile`. Note this is **necessary but not sufficient** — the server also
hardcodes `graph.facebook.com/v26.0`, so it stays unusable for IG until Path 1 lands.

## Non-Meta platforms

| Platform | Verdict | Note |
|---|---|---|
| Reddit | 🚫 NO-GO | free tier is non-commercial (Legal) |
| X / Twitter | 💰 paid only | free tier dead Feb 2026; needs founder/CFO |
| Pinterest / Telegram / YouTube / LinkedIn | not started | CRO ledger order: Pinterest ≥ Telegram > YouTube > LinkedIn |

Any new platform needs a compliance-register entry (`trend_predictor/docs/legal/compliance-register.md`)
from Legal **before** the first API call.

## Meta FB-login switch-over — state 2026-08-19 (paused, resumable)

**Done:**
- Facebook Page **TrendRadar** (`61593158354383`) created + linked to @trendradar.in.
- Generated a Facebook-Login token in Graph API Explorer (scopes: business_management,
  ads_management, instagram_basic, instagram_content_publish, instagram_manage_comments,
  instagram_manage_insights) and **exchanged it for a long-lived (~60-day) token**.
- Stored in gitignored `.env`: `META_APP_ID`, `META_APP_SECRET`, `FB_LONG_LIVED_TOKEN`,
  `FB_USER_TOKEN` (= long-lived). `META_APP_ID`/`META_APP_SECRET` also mirrored to user-level
  Windows env vars. Helper: `scripts/finish_meta_switchover.py`.

**Not done yet (deferred by founder):**
- `INSTAGRAM_USER_ID` for the Graph (facebook.com) side is unresolved: `/me/accounts` returned
  0 pages because the token lacks **`pages_show_list`**. Two ways to finish later:
  1. Re-run `scripts/finish_meta_switchover.py` — it now falls back to reading the Page node
     `61593158354383` directly (works if `business_management` can read the Page; no regen).
  2. Otherwise regenerate the token in Graph API Explorer **with `pages_show_list`** added, then
     re-run the script.
- Once `INSTAGRAM_USER_ID` (the IG **business-account** id, which may differ from the IG-login
  id `27870001472663258`) is in `.env` + env vars, restart Claude Code to activate the OSS
  `meta-mcp` interactive control plane (66 IG+Threads tools) + Ads.

**Unaffected / still running:** the production publish pipeline uses the existing **IG-login**
token on `graph.instagram.com` (unchanged). Posting resumes on schedule; the FB-login work above
is additive and does not touch the pipeline until we deliberately flip `IG_AUTH_MODE`.
