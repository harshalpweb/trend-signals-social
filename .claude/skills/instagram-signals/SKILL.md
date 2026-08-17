---
name: instagram-signals
description: Pull this week's top trend_predictor signals and turn them into Instagram content angles (which entity/product/category to feature, with the supporting numbers). Use at the start of the weekly content-generation routine, before writing any caption or design. Read-only against trend_predictor — never modifies it.
---

# Pull This Week's Signals

Reads `trend_predictor`'s current state **read-only, locally** — nothing about the engine, its DB, or its methodology leaves this step except the finished numbers you choose to feature. Never touches trend_predictor's git history or writes to its DB.

## Where trend_predictor lives

This skill runs from a session that also has access to the `trend_predictor` repo checkout (sibling directory, e.g. `../trend_predictor` relative to `trend-signals-social`, or wherever it's checked out locally — confirm the path if unclear, don't assume). It has its own virtualenv (`trends_predictor_env`) with the `trendpredictor` package installed.

## How to pull signals

Two real, current entry points exist in `trendpredictor` (verify these still exist before relying on them — the engine evolves; grep `src/trendpredictor/store.py` and `src/trendpredictor/scoring/ranker.py` for current signatures if this skill looks stale):

1. **Top movers / composite scores** — `trendpredictor.store.Store(DB_PATH).read_latest_scores(market)` (see `trendpredictor.config.DB_PATH`, `MARKET`). Returns rows with `entity`, `composite`, `momentum`, `conviction`, and an `agreeing` list (which independent signal families agree this entity is moving) — this is the same data the internal dashboard's `/api/scores` route serves (`src/trendpredictor/dashboard/app.py`, `_scores_with_sparklines`).
2. **Festival-calendar proximity** — `trendpredictor.festival.upcoming(today, horizon_days=90)` and `trendpredictor.festival.order_by_dates(...)` — surfaces upcoming India festivals and their commercial "order-by" windows, useful for Sat digest / trend-jacking timing.

Run a short read-only Python snippet (via the venv) rather than guessing at values — e.g.:

```python
from trendpredictor.store import Store
from trendpredictor.config import DB_PATH, MARKET
store = Store(DB_PATH)
top = sorted(store.read_latest_scores(MARKET), key=lambda r: r["composite"], reverse=True)[:10]
```

## Turning scores into a content angle

For each of Mon/Wed/Fri (signal posts), pick ONE entity from the top movers, prioritizing by:
1. **`conviction` score** over raw `composite` — conviction reflects agreement across independent signal families, which is exactly the "receipts" story (see `references/algorithm.md` in `instagram-growth` — conviction-backed claims are what survive scrutiny in replies).
2. Recency of the move (`momentum`, `eta`/`recent_break` if present) — prefer things that just started moving over long-since-obvious trends.
3. Do not repeat an entity featured in the last 2 weeks unless there's a genuinely new development (a follow-up "here's what happened next" angle is fine and on-brand for build-in-public; a flat repeat is not).

For Sat (digest): pull the top 3-5 movers of the week as a leaderboard, not just one entity.

For Sun (build-in-public): this doesn't need a signal pull — it's methodology/process content. Skip this skill for Sunday posts.

## Output

Hand off a short structured angle per post — not a caption yet, just the raw material:

```
entity: <name>
composite: <score>
conviction: <score>
agreeing_families: [<list>]
festival_context: <upcoming festival + order-by date, if relevant this week, else null>
angle: <one sentence — why this entity, why now>
```

This feeds directly into `instagram-caption` (writes the words) and `instagram-carousel` (writes the numbers into the template's data slides). Never fabricate a number that isn't actually in `read_latest_scores` output — the entire brand rests on these being real.

## Forward-dated predictions gate

Per `instagram-growth/config.yaml`, `forward_dated_predictions: false`. Only feature *current* signals ("what's trending now"), never "we predict X will happen" framing, until that config flag flips — which requires the founder to have privately validated trend_predictor's lead time first. If you're unsure whether a given angle crosses that line, err toward "here's what's moving right now" framing.
