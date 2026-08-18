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
| Health probe | `py -3.12 scripts/check_token.py` (exit 0 live / 2 OAuthException / 3 config / 4 network) |
| Graph client | `scripts/ig_common.py` — all three scripts go through it: token in an `Authorization: Bearer` header (never a query string), 30s timeout, every error string redacted. Tests: `py -3.12 -m pytest -q` (offline). |
| Publishing cap | ~25 API posts per rolling 24h — `GET /{ig-user-id}/content_publishing_limit` before any batch |
| Status | 🔴 **INCIDENT — `OAuthException code 200 "API access blocked."`** |
| Next action | **Path 1** — founder links a Facebook Page to @trendradar.in and moves the app to the Facebook-Login-for-Business Instagram flow |

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

**Blocked on:** founder OAuth for the `meta-devtools` MCP (`claude mcp login meta-devtools`),
which is what exposes compliance findings and App Review status. Until then the cause is
inferred, not read.

**Impact:** no post has actually exercised the token since 2026-08-17 — every hourly run since
has printed "No due posts", so the restriction has been invisible. The next genuinely due post
would have failed silently on a green run before today's `publish.yml` change.

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
| Meta Ads | `meta-ads` MCP registered at user scope, **needs founder OAuth**; no ad account / payment method attached (deliberate — spend stays impossible until the founder unlocks it) |
| Webhooks | none subscribed |

## MCP control surfaces

| Server | Scope | Tools | Auth state |
|---|---|---|---|
| `meta` (OSS `@mikusnuz/meta-mcp` v2.1.x, MIT) | inline in `.claude/agents/chief-social-media-manager.md` | 66 (33 IG, 27 Threads, 6 app/token/webhook) | env-var driven; **currently broken — see defect below** |
| `meta-devtools` (official) | user (`~/.claude.json`) | app settings, compliance findings, App Review, rate limits, webhooks | ❌ needs founder OAuth |
| `meta-ads` (official) | user (`~/.claude.json`) | ~29 ads tools | ❌ needs founder OAuth |

**Open defect (found 2026-08-19):** the `meta` server's `${INSTAGRAM_ACCESS_TOKEN}` /
`${INSTAGRAM_USER_ID}` placeholders are **not expanded** — a live call returned
`GET /${INSTAGRAM_USER_ID} (400) … code 190 "Cannot parse access token"`, i.e. the literal
placeholder string was sent as the path and the token. The variables *are* present in
`HKCU\Environment`; they were set with `setx` after this Claude Code process started, and
Windows processes do not pick up `setx` changes retroactively. **Fix: restart Claude Code.**
Re-verify with `mcp__meta__ig_get_profile` before concluding anything about the OSS client.

## Non-Meta platforms

| Platform | Verdict | Note |
|---|---|---|
| Reddit | 🚫 NO-GO | free tier is non-commercial (Legal) |
| X / Twitter | 💰 paid only | free tier dead Feb 2026; needs founder/CFO |
| Pinterest / Telegram / YouTube / LinkedIn | not started | CRO ledger order: Pinterest ≥ Telegram > YouTube > LinkedIn |

Any new platform needs a compliance-register entry (`trend_predictor/docs/legal/compliance-register.md`)
from Legal **before** the first API call.
