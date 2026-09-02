"""Meta Ad Library (web UI, IN, active, all ads) daily snapshot collector.

STATUS: PRE-STAGED, DORMANT. HARD-GATED on Legal/founder D6 clearance.
This script REFUSES to run until the approval artifact exists (see GATE below).
Pre-staged 2026-08-20 by CSMM so that on the day D6 clears, collection starts
same-day: founder latency, not build time, is the only remaining delay.

WHY GATED: Legal ruling 2026-08-20 — agent/automated browsing of the Ad
Library web UI is automated collection under Meta ToS regardless of cadence;
D6 needs explicit founder approval (COM spec out-of-scope line). Nothing here
may execute before that clears.

GATE (the only switch):
    docs/approvals/D6-ad-library.approved   (repo-relative, in this repo)
  must exist AND contain the word APPROVED plus a date line. It is created by
  the CoS only after the founder clears D6. No env-var override on purpose —
  an env var is too easy to set by accident.

IDENTITY DECOUPLING (account-safety invariants — do not weaken):
  * Fresh, cookie-less Chromium context every run. NEVER load a profile,
    NEVER inject Meta cookies or tokens, NEVER log in.
  * If a keyword page presents a login wall, record {"login_wall": true}
    and move on. If >50% of keywords hit login walls, exit 4 (surface it;
    a persistent login wall means this path is dead — escalate, never
    authenticate around it).
  * Run from this machine (residential egress), never from a runner that is
    associated with our Business Manager or holds Meta secrets in env.

ACTIVATION (day D6 clears — run these two commands, nothing else):
  py -3 -m pip install playwright && py -3 -m playwright install chromium
  schtasks /create /tn TrendRadar-AdLibSnapshot /sc daily /st 09:20 ^
    /tr "py -3 C:\\Users\\2026\\Documents\\trend-signals-social\\platforms\\meta_ad_library\\collect_adlib_snapshot.py"
  (then one manual run to verify: exit 0 and a JSONL file in snapshots/)

CADENCE: 1x daily. ~12s polite dwell per keyword, <=60 keywords => ~12-15 min.
STORAGE: platforms/meta_ad_library/snapshots/adlib_YYYY-MM-DD.jsonl
  Append-only point-in-time rows; one row per keyword per day:
  {snapshot_ts, keyword, results_count, login_wall, ads:[{library_id,
   started_running, page_name}], error}
BUDGET: Rs.0 — local machine, no API, no paid service.
EXIT CODES: 0 ok; 3 D6 gate closed; 4 login-wall majority; 5 error majority.
"""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
GATE = REPO / "docs" / "approvals" / "D6-ad-library.approved"
WATCHLIST = HERE / "watchlist.txt"
SNAPDIR = HERE / "snapshots"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def gate_check() -> None:
    if not GATE.exists() or "APPROVED" not in GATE.read_text(encoding="utf-8", errors="replace"):
        print(f"D6 NOT CLEARED — refusing to run. Gate file required: {GATE}", file=sys.stderr)
        sys.exit(3)


def load_watchlist() -> list[str]:
    kws = []
    for line in WATCHLIST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            kws.append(line)
    return kws


def parse_ads(body_text: str) -> list[dict]:
    """Best-effort parse of visible ad cards: Library ID + start date + page."""
    ads = []
    # Cards render as "Library ID: 123... Started running on <date>" blocks.
    for m in re.finditer(
        r"Library ID:?\s*(\d{6,})(?:.{0,400}?Started running on\s+([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}))?",
        body_text, re.S,
    ):
        ads.append({"library_id": m.group(1), "started_running": m.group(2)})
        if len(ads) >= 30:
            break
    return ads


def main() -> int:
    gate_check()
    from playwright.sync_api import sync_playwright  # import after gate: dep not needed while dormant

    kws = load_watchlist()
    SNAPDIR.mkdir(exist_ok=True)
    out = SNAPDIR / f"adlib_{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"
    walls = errs = 0
    with sync_playwright() as p, out.open("a", encoding="utf-8") as fh:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA, locale="en-US",
                                  extra_http_headers={"Accept-Language": "en-US,en;q=0.9"})
        assert not ctx.cookies(), "identity-decoupling violated: context has cookies"
        page = ctx.new_page()
        for kw in kws:
            row = {"snapshot_ts": datetime.now(timezone.utc).isoformat(),
                   "keyword": kw, "results_count": None, "login_wall": False,
                   "ads": [], "error": None}
            url = ("https://www.facebook.com/ads/library/?active_status=active"
                   f"&ad_type=all&country=IN&q={kw}&search_type=keyword_unordered&media_type=all")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(7)
                for _ in range(2):
                    page.mouse.wheel(0, 5000)
                    time.sleep(2.5)
                txt = page.inner_text("body")
                if re.search(r"log in|create new account", txt[:2000], re.I) and "results" not in txt.lower():
                    row["login_wall"] = True
                    walls += 1
                else:
                    m = re.search(r"~?([\d,]+)\s+results?", txt)
                    row["results_count"] = int(m.group(1).replace(",", "")) if m else None
                    row["ads"] = parse_ads(txt)
            except Exception as e:  # no secrets exist in this process; str(e) is safe
                row["error"] = str(e)[:300]
                errs += 1
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
        browser.close()
    n = len(kws)
    print(f"snapshot done: {n} keywords, {walls} login walls, {errs} errors -> {out}")
    if n and walls / n > 0.5:
        return 4
    if n and errs / n > 0.5:
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
