---
name: instagram-signals
description: Pull this week's top trend_predictor signals and turn them into Instagram content angles (which entity/product/category to feature, with the supporting numbers). Use at the start of the weekly content-generation routine, before writing any caption or design. Read-only against trend_predictor — never modifies it.
---

# Pull This Week's Signals

Reads `trend_predictor`'s current state **read-only, locally** — nothing about the engine, its DB, or its methodology leaves this step except the finished numbers you choose to feature. Never touches trend_predictor's git history.

## Where trend_predictor lives and which interpreter to use

Sibling checkout at `C:\Users\2026\Documents\trend_predictor` (confirm this path if it's moved). **Use the `py -3.12` launcher, not the `trends_predictor_env` venv** — as of 2026-08-17 the `trendpredictor` package is only importable from the global `py -3.12` interpreter; the venv raises `ModuleNotFoundError`. Verify this is still true before relying on it (`py -3.12 -c "import trendpredictor"` from the trend_predictor directory) — venvs get fixed.

## How to pull signals

Two real entry points in `trendpredictor` (verify these still exist before relying on them — grep `src/trendpredictor/store.py` and `src/trendpredictor/scoring/ranker.py` for current signatures if this skill looks stale; the engine evolves):

1. **Top movers / composite scores** — `trendpredictor.store.Store(DB_PATH).read_latest_scores(market)`. **`Store()` opens the DB read-write and runs migrations on construction** (`store.py` `__init__`) — this is NOT a read-only connection despite the name of this skill. To avoid any risk of colliding with the daily collection run, open your own read-only connection instead:
   ```python
   import sqlite3, json
   from trendpredictor.config import DB_PATH, MARKET
   conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
   conn.row_factory = sqlite3.Row
   ```
   and query the same table `Store.read_latest_scores` reads from directly (check `store.py` for the exact query/table name — do not guess it, read the source). Each row has keys `entity`, `composite`, `momentum`, `conviction`, and `detail` — **`detail` is a JSON *string*, not a dict**: `json.loads(row["detail"] or "{}")`. The `agreeing` list (which signal families corroborate this entity) and `lenses` (with `eta`/`recent_break`) live *inside* that parsed `detail`, not as top-level row keys. Not every row has a `composite` key (some are momentum-only) — always use `row.get("composite", 0.0)`, never `row["composite"]`.
2. **Festival-calendar proximity** — `trendpredictor.festival.upcoming(today, horizon_days=90)` and `trendpredictor.festival.order_by_dates(...)` — surfaces upcoming India festivals and their commercial "order-by" windows, useful for Sat digest / trend-jacking timing.

## The "receipts" claim must match the actual data — this is the whole brand

`conviction_score` (`scoring/conviction.py`) is `len(agreeing) + 0.1 * momentum` — so a high conviction score does **not** by itself mean multiple signal families agree; check `len(detail["agreeing"])` directly. As of 2026-08-17, essentially every entity in the live DB has `agreeing == ['search']` — a single source. **Never claim "multiple signals agree" or write multi-source-corroboration language (in captions or footer text) unless `len(detail["agreeing"]) >= 2` for that specific entity, checked at generation time, not assumed.** If the strongest entity this week only has one agreeing family, that's fine — feature it with honest single-source framing ("per Google Trends search data," not "confirmed across signals"). A false corroboration claim is worse for this brand than a smaller one.

## Turning scores into a content angle

For each of Mon/Wed/Fri (signal posts), pick ONE entity from the top movers, prioritizing by:
1. **Real corroboration first**: prefer entities with `len(detail["agreeing"]) >= 2` when any exist that week — that's the strongest, honestly-multi-source "receipts" story. If none exist, fall back to the single strongest single-source entity by `composite`/`momentum`, with correspondingly honest caption framing (see above).
2. Recency of the move (`momentum`, `detail["lenses"].get("eta")`/`detail["lenses"].get("recent_break")` if present) — prefer things that just started moving over long-since-obvious trends.
3. Do not repeat an entity featured in the last 2 weeks unless there's a genuinely new development. Check both this run's new queue entries **and** `content/posted/*/*.json`, `content/failed/*/*.json` (posted/failed posts are nested one directory per post, e.g. `content/posted/2026-08-24-signal-01/2026-08-24-signal-01.json` — a flat `content/posted/*.json` glob matches nothing).

For Sat (digest): pull the top 3-5 movers of the week as a leaderboard, not just one entity — state each entity's actual `agreeing` count honestly rather than a blanket claim for the whole digest.

For Sun (build-in-public): this doesn't need a signal pull — it's methodology/process content. Skip this skill for Sunday posts.

## Output

Hand off a short structured angle per post — not a caption yet, just the raw material:

```
entity: <name>
composite: <score, or null if this row has no composite>
conviction: <score>
agreeing_families: [<actual list from detail.agreeing>]
festival_context: <upcoming festival + order-by date, if relevant this week, else null>
angle: <one sentence — why this entity, why now>
```

This feeds directly into `instagram-caption` (writes the words) and `instagram-carousel` (writes the numbers into the template's data slides). Never fabricate a number, and never state or imply corroboration that `agreeing_families` doesn't actually support.

## Forward-dated predictions gate

Per `instagram-growth/config.yaml`, `forward_dated_predictions: false`. Only feature *current* signals ("what's trending now"), never "we predict X will happen" framing, until that config flag flips — which requires the founder to have privately validated trend_predictor's lead time first. If you're unsure whether a given angle crosses that line, err toward "here's what's moving right now" framing.
