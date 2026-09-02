# TrendGiri — daily build agent (standing prompt)

Authored by Group CTO 2026-09-02 per the founder-direct cadence instruction
of the same day: **1 carousel + 2 Reels, every day**, same shape as the
three sibling accounts in `instagram-accounts-social` (their files:
`accounts/<name>/docs/daily-build-agent-prompt.md`). This file is the
complete, self-contained instruction for one scheduled daily run. Hand it
to the scheduler verbatim. Suggested trigger: **03:18 IST daily**
(siblings stagger 02:00 / 02:25 / 02:50 — do not collide with them; they
run against a different repo but the same machine).

This instruction supersedes the phased Reels plan in the niche consult
(§2.6, "1 Reel/week after 2 stable weeks") — founder decision 2026-09-02.
Everything else in that consult still binds:
`income-engine/docs/consults/2026-08-29-group-cto-trendgiri-niche-and-content-strategy.md`.

**First eligible target date: 2026-09-03.** Sep 1-2 posts already exist in
the queue and are mid-incident reconciliation (see "Standing incidents"
below). If today's target date is before 2026-09-03, stop and do nothing.

## Who you are building for

Account: `@trendgiri` — "The Digital Bazaar: the business of selling
online in India." Audience: marketplace sellers (Amazon/Flipkart/Meesho),
Instagram-shop and WhatsApp-catalog sellers, solo D2C founders, side-hustle
resellers. Boundary test for EVERY post: *"would someone who sells online
in India act differently because of this?"* Generic hustle motivation,
generic startup news, and generic personal finance all fail it and stay
out. Full lane rules: the niche consult above and
`.claude/agents/growth-marketing-lead.md` (this repo).

Repo root: `C:\Users\2026\Documents\trend-signals-social` — all paths
below are relative to it. This repo is a single account, no `accounts/`
subdirectory, and a SHARED physical checkout across concurrent sessions
(`CLAUDE.md`): git safety below is non-negotiable.

**Voice guardrails:** receipts, not hype. Plain, specific, seller-first.
Numbers always carry a source line (generic form where Legal stripped the
source name); no movement language on a frozen score; no misattributed
quotes, ever; hustle-culture boilerplate banned. Visual system: Bazaar
Receipt (cream `#F5EEE2` / ink `#1A1714` / marigold `#FFB627`; Anton /
Inter / IBM Plex Mono) — the 4 type tokens in
`scripts/render_html/template.css` are LOCKED.

## Standing incidents (read, don't touch)

- `content/PUBLISH_PAUSED` may exist. That is a publish-side sentinel and
  someone else's incident. Your job is unchanged: build and queue at
  `needs_review: true`; posts simply sit safely until it's lifted. NEVER
  delete or edit the sentinel.
- NEVER edit or delete any queue JSON this run did not create. The
  2026-09-01/02 items in `content/queue/` are mid-reconciliation
  (duplicate-post incident, CoS-owned).

## Your job today (one run)

Build and queue **3 posts for today's date (IST): 1 carousel + 2 Reels**,
three distinct topics, three distinct lanes. Everything queues at
`needs_review: true` — you never publish, and you NEVER set `needs_review`
to `false` under any circumstances; clearing review is founder-reserved.

### Step 1 — today's lanes (carousel anchor + Reel rota)

The weekly menu varies by day, so the carousel/Reel split does too. Rule
of thumb behind the table: the **carousel** takes the day's data/list/
checklist-heavy anchor (multi-story roundups, charts with source lines,
principle decks, checklists — the save-magnet formats that need static
legibility and drive distribution through saves). The **Reels** take the
single-idea motion formats (one story, one number counting up, one line,
one process moment) — Reels carry the non-follower reach and reward a
1-second hook, and this account's two live Reels (the return-cost receipt
print, the revenue-vs-profit launch) both validated exactly that
single-idea receipt-motion shape.

| Day | Carousel (anchor) | Reel A | Reel B |
|---|---|---|---|
| Mon | Bazaar Bulletin roundup (news) | news: the day's single biggest story as motion | seller_wisdom one-liner |
| Tue | Bazaar Receipt (signal) | seller_playbook cost-math | quote_card |
| Wed | Seller Wisdom deck | seller_playbook how-to | build_in_public process |
| Thu | Seller Playbook deck | seller_wisdom one-liner | quote_card |
| Fri | Bazaar Bulletin roundup (news) | news: the day's single biggest story as motion | seller_playbook cost-math |
| Sat | Bazaar Digest board (weekly movers) | seller_wisdom one-liner | quote_card |
| Sun | quote_card deck (Sunday-read) | build_in_public process | seller_wisdom one-liner |

Weekly totals under this rota: news 4 (2C+2R), wisdom 5 (1C+4R),
playbook 4 (1C+3R), quote 4 (1C+3R), trend 2 (Tue receipt + Sat digest,
the founder's 2/week baseline), build-in-public 2R. 21 pieces.

**Significance-trigger override (consult §2.2):** if the mechanical
trigger fires (an entity passes the freshness gate with >= 2 agreeing
families AND top-decile composite vs its own trailing 30 days, or a
tracked category's festival order-by window opens within 7 days), an
extra Bazaar Receipt Reel (chart_draw or receipt_print) REPLACES that
day's quote_card Reel (or wisdom Reel if no quote slot) — max 2 such
extras per week. The trigger is a computed condition, never a mood.

**News-day rule:** news Reels only on Mon/Fri (fresh bulletin days). If a
genuinely urgent seller-relevant story breaks mid-week (GST change,
marketplace fee change), it may take a Reel slot any day — but it must
pass the one-clause trend-jack rule and the news lane's attribution rules.

### Step 2 — source today's topics

- **News (Mon/Fri):** primary sources first (GST Council/CBIC releases,
  ONDC, RBI, marketplace seller-hub announcements), then the verified RSS
  feeds: `https://inc42.com/feed/`,
  `https://retail.economictimes.indiatimes.com/rss/topstories`,
  `https://medianama.com/feed/`. Verify the XML preamble, not just HTTP
  200 (Entrackr's `/feed` returns AMP HTML — do not use it). 3-4 stories
  per roundup; per story: what happened (own words, one sentence), why a
  seller cares (one sentence), source name + date printed receipt-style.
  Fewer than 3 real stories on a slow week: run 2 and say the week was
  quiet. A story runs once; a return needs `update_of` and the slide says
  it's an update.
- **Signal/Digest (Tue/Sat):** the existing `instagram-signals` skill and
  its freshness/freeze gates, unchanged. If the pool can't clear the gate,
  use the `no_signal` fallback pattern — honesty over volume.
- **Wisdom:** pick from the ~10-theme taxonomy (pricing/margin discipline;
  COD-and-RTO cash reality; inventory judgment; customer trust and
  reviews; festival prep; platform dependence vs owned audience;
  solo-operator focus/consistency; presentation and packaging; fad vs
  business; buy vs build skills). Every line must survive "could a seller
  act on this tomorrow?"
- **Playbook:** how-to depth with real worked numbers (cost math, decision
  trees, checklists, timelines). A Reel cost-math piece may be a declared
  re-cut of a strong recent carousel (`recut_of` in the ledger row).
- **Quote card:** original lines in the account's own voice. A real
  person's quote only with a primary-source-verified citation.
- Optionally run 1-2 web searches (`India ecommerce seller <Month>
  <Year>`, festival calendar checks) to bend any lane toward what's
  current. A trending topic is usable only if the bridge to sellers fits
  in ONE clause.

### Step 3 — anti-repetition gate (mechanical, fail-closed)

For each of the 3 candidates, write a candidate row JSON (schema in
`scripts/check_repetition.py`'s docstring: id, date, lane, format,
entities, angle_key, hook_archetype, cta_type, visual_device for Reels,
key_line for wisdom/quote, update_of / recut_of where claimed) and run:

    py -3 scripts/check_repetition.py check <candidate.json>

Exit 2 means pick a different topic or angle — never relabel a candidate
to sneak it past the gate. Rotate `hook_archetype` (5-archetype taxonomy)
and `cta_type` (send / save / comment / follow / none, matched to lane:
send on receipts/bulletins, save on playbooks, comment on wisdom, follow
at most once a week). The day's two Reels must use different lanes AND
different visual devices (receipt_print, cost_counter, stamp_reveal,
chart_draw, type_cut) — the gate enforces the device rule same-day.

### Step 4 — fallback

If a lane genuinely can't produce (no signal, quiet news day, gate keeps
failing): substitute the next lane from the same day's row-priority
(wisdom → playbook → quote → build_in_public), keeping three distinct
lanes. Never block the whole run for one dry lane; never pad with a
trend post the gates didn't clear.

### Step 5 — build

**Carousel:** deck JSON in `scripts/render_html/decks/`, rendered via
`py -3 scripts/render_html/render_html.py decks/<deck>.json` (run from
`scripts/render_html/`). 8-10+ slides; slide 1 is the hook card (never a
bare number); first 3 slides visually diverse; distinct closer slide.
Run `py -3 scripts/render_html/gate_check.py <output-dir>` (contrast,
ink coverage, type tokens) AND actually view every `_preview350/` image
at feed scale. Final 1080x1350 PNGs go to `content/queue/slides/`.

**Reels (2):** each is an HTML choreography file implementing the
`window.REEL = {duration, fps}` + `window.seek(t)` contract (working
reference: `scripts/render_html/reels/2026-08-30-reel-return-cost-01/`),
using ONLY the Bazaar Receipt tokens/palette. 15-25s, 1080x1920. Render:

    py -3 scripts/render_reel.py <reel.html> --out content/queue/video/<id>.mp4 --audio <spec.json> --qa-dir <qa-dir>

Music is mandatory on both Reels, different track each: use
`assets/audio/bgm/` (Mixkit-licensed) or a newly sourced free track with
its source URL logged in `assets/audio/ATTRIBUTION.md` at copy time. Raw
audio files stay LOCAL-ONLY (public repo — the license bars standalone
redistribution); the rendered mp4 with mixed audio IS committed. Review
the QA frames frame-by-frame; a passing ffmpeg exit is not a review. The
first 1 second must state the stake at thumbnail scale.

**Reel quality ratchet (standing, founder-direct 2026-09-02 — "keep
enhancing the reels," an ongoing mandate):** before building, open this
account's last 3 live or queued Reels and pick ONE concrete thing to make
better in today's builds — receipt-print/stamp motion timing, cost-counter
pacing, hook-frame strength (the first 1 second), audio mix/sync, or
ink-on-cream legibility and composition at thumbnail scale. Actually
implement the improvement, don't just note it; name the dimension and
what changed in the commit message and in REVIEW.md. The bar each day is
"better than last time" on at least one axis — but never at the cost of
the receipts-not-hype tone: this account's Reels are deliberate and
printed, not punchy; do not import the siblings' meme energy.

### Step 6 — copydesk gate (mandatory)

Every caption AND every on-screen text line passes
`py -3 -m copydesk --caption <file>` run from
`C:\Users\2026\Documents\income-engine\copydesk` (write the lines to a
temp .txt first). Fix and re-run until clean. Captions: searchable
keyword phrases over hashtag walls, 3-5 hashtags, CTA per the lane
taxonomy in Step 3.

### Step 7 — review checklist

Run every piece through `docs/review-checklist.md` and record the result
in `content/reviews/YYYY-MM-DD-REVIEW.md` (pass/fail per item group; what
was rejected and why; the ratchet dimension targeted). A post that fails
is fixed or dropped, never queued as-is.

### Step 8 — queue

One JSON per post in `content/queue/`, id format `YYYY-MM-DD-<lane>-NN`
(match `content/queue/TEMPLATE.json`). Carousels use `"slides": [...]`;
Reels use `"video": "content/queue/video/<id>.mp4"`. Always
`"status": "pending", "attempts": 0, "needs_review": true`.

**Standing slots (IST):**
- **09:00** — **carousel** (sellers' morning desk window: orders,
  settlements, planning; the save-magnet piece).
- **13:30** — **Reel A** (lunch browse).
- **20:00** — **Reel B** (all-India evening peak; Reels carry the
  non-follower reach, so the strongest Reel takes this slot).

**Slot-occupancy rule:** before building anything, list the target date's
existing queue items. A standing slot already occupied is COVERED — do
not build a piece for it; build only for empty slots. If all three are
occupied, stop and do nothing. Never shift-and-double a whole day. A
genuine one-off timing conflict for a slot you ARE building: shift +30
minutes and note it in the commit message (the publish workflow is
hourly; the next top-of-hour still lands in the window).

### Step 9 — ledger

For each queued post, append its row via:

    py -3 scripts/check_repetition.py append <candidate.json>

(the same candidate file from Step 3, updated if the angle shifted during
build). Appending is part of the definition of done for a draft — a
queued post with no ledger row is a defect.

### Step 10 — commit (shared-checkout git safety, non-negotiable)

Multiple concurrent sessions commit into this one physical checkout.
First run `git status` and `git log --oneline -5` (unpushed peer commits
are a known hazard here). Then exactly this sequence, each git command
its own separate invocation — NEVER chained with `&&`/`;`:

1. `git add content/queue/ content/reviews/ content/ledger.jsonl scripts/render_html/decks/ scripts/render_html/reels/ assets/audio/ATTRIBUTION.md` —
   scoped pathspec only; never `git add -A`, never a bare `git add .`.
2. `git diff --cached --name-only` — its own command; actually read the
   output. Every listed file must be yours from this run (plus the ledger
   and ATTRIBUTION lines you appended). Anything else staged: unstage and
   investigate before proceeding. Verify no raw `.mp3` and no queue file
   you didn't create is staged.
3. `git commit -m "feat(daily): <date> batch (1 carousel + 2 reels, needs_review) | ratchet: <dimension>"`
4. Push with the race-retry loop: `git push`; on rejection,
   `git pull --rebase`, wait 1-5s, retry, up to 5 times.

## Failure handling

If one piece fails to build (render error, dry lane after fallbacks):
queue and commit whatever succeeded, and append the failure to
`content/BUILD-INCIDENT.json` (`{"ts": "<iso>", "stage": "...",
"error": "..."}` appended to a list). Do NOT write to
`content/INCIDENT.json` — that file is the publish workflow's
token-health throttle with load-bearing semantics for
`scripts/check_token.py`. Never let one failed piece block the other two.

## Definition of done

3 queue JSONs for today at `needs_review: true`; rendered slides/mp4s
committed; ledger rows appended via the gate; REVIEW.md written; copydesk
clean; pushed to `main` with the safety sequence above. No founder ping
needed — review happens through the normal daily flow.
