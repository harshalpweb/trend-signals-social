#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed anti-repetition gate over content/ledger.jsonl.

Implements the content-ledger mechanism designed in
income-engine/docs/consults/2026-08-29-group-cto-trendgiri-niche-and-content-strategy.md
(section 2.4), built 2026-09-02 by Group CTO as part of the daily-build system
(docs/daily-build-agent-prompt.md).

The ledger is one JSON object per line, one line per queued-or-published post:

    {"id": "...", "date": "YYYY-MM-DD", "lane": "...",
     "format": "carousel"|"reel", "entities": ["slug", ...],
     "angle_key": "...", "hook_archetype": ...|null, "cta_type": ...|null,
     "visual_device": ...|null, "key_line": ...|null,
     "update_of": ...|null, "recut_of": ...|null,
     "status": "queued"|"posted", "ig_post_id": ...|null,
     "permalink": ...|null, "backfill": true|absent}

Historical (backfilled) rows may carry null hook_archetype/cta_type/
visual_device because those taxonomies postdate the posts; a NEW candidate
must fill every classification field. Exact-key matching against a fixed
vocabulary on purpose, not fuzzy NLP: a vocabulary the drafter must classify
into is auditable at Rs.0; embedding similarity is not.

Windows (per the consult, plus dated implementation defaults):
  * signal entities: 14 days against prior signal rows (the existing 2-week
    entity no-repeat rule, now enforced from the ledger). digest rows are
    exempt as candidates: a weekly board legitimately re-lists entities.
  * seller_wisdom angle_key: 60 days; its exact key_line: forever.
  * quote_card angle_key: 60 days; its exact key_line (the quote): forever.
  * news angle_key: once ever, unless the candidate names `update_of` (a
    prior ledger id or angle_key) AND that prior row exists -- and the slide
    must say it's an update (review-checklist item, not enforceable here).
  * seller_playbook angle_key: 90 days.
  * build_in_public angle_key: 60 days; signal/digest angle_key: 14 days;
    product_launch angle_key: 30 days (implementation defaults, 2026-09-02 --
    the consult specified only the first four).
  * hook_archetype: may not equal the most recent ledger row's (non-null).
  * cta_type: may not run 3 distinct days in a row.
  * visual_device (Reels): may not repeat between two Reels on the same date
    (the same-day scene/prop rule, TrendGiri form).
  * recut_of: a declared cross-format derivative (the consult's "re-cut the
    week's best deck" Reels pattern) bypasses the angle_key window and the
    key_line check IF the named row exists and its format differs from the
    candidate's. Nothing else is bypassed.

Fail-closed: a missing/corrupt ledger, an unknown lane/format/hook/cta/
device, a missing required field, or a duplicate id all FAIL (exit 2) --
never silently pass.

Usage:
    py -3 scripts/check_repetition.py check  <candidate.json> [--ledger PATH]
    py -3 scripts/check_repetition.py append <candidate.json> [--ledger PATH]

`append` re-runs the full check and refuses to write on any violation.
Exit 0 = clean; exit 2 = violation or ledger/candidate error.
"""
import argparse
import json
import re
import sys
from datetime import date as _date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LEDGER = REPO_ROOT / "content" / "ledger.jsonl"

LANES = {
    "signal",
    "digest",
    "news",
    "seller_wisdom",
    "seller_playbook",
    "build_in_public",
    "quote_card",
    "product_launch",
}
FORMATS = {"carousel", "reel"}
HOOK_ARCHETYPES = {
    "stake_statement",
    "mid_story_open",
    "contrarian_receipt",
    "cost_of_ignoring",
    "count_promise",
}
CTA_TYPES = {"send", "save", "comment", "follow", "none"}
VISUAL_DEVICES = {
    "receipt_print",
    "cost_counter",
    "stamp_reveal",
    "chart_draw",
    "type_cut",
}

ENTITY_WINDOW_DAYS = 14
ANGLE_WINDOW_DAYS = {
    "seller_wisdom": 60,
    "quote_card": 60,
    "seller_playbook": 90,
    "build_in_public": 60,
    "signal": 14,
    "digest": 14,
    "product_launch": 30,
    # "news" is handled separately: once ever unless update_of.
}
CTA_MAX_CONSECUTIVE_DAYS = 2

EXIT_OK = 0
EXIT_FAIL = 2


class LedgerError(Exception):
    """The ledger (or candidate) itself is unusable -- always a failure."""


def _norm_line(text: str) -> str:
    """Normalize a key_line for exact-match-forever comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(value, where: str) -> _date:
    try:
        return _date.fromisoformat(value)
    except (TypeError, ValueError):
        raise LedgerError(f"{where}: bad or missing date {value!r}")


def load_ledger(path: Path) -> list:
    if not path.exists():
        raise LedgerError(
            f"ledger not found at {path} -- fail closed; backfill it first "
            "(see docs/daily-build-agent-prompt.md)"
        )
    rows = []
    for lineno, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LedgerError(f"ledger line {lineno} is not valid JSON: {exc}")
        for field in ("id", "date", "lane", "format", "angle_key"):
            if not row.get(field):
                raise LedgerError(f"ledger line {lineno}: missing {field!r}")
        row["_date"] = _parse_date(row["date"], f"ledger line {lineno}")
        rows.append(row)
    return rows


def validate_candidate(cand: dict) -> None:
    """Vocabulary + required-field validation. Raises LedgerError."""
    for field in ("id", "date", "lane", "format", "angle_key",
                  "hook_archetype", "cta_type"):
        if not cand.get(field):
            raise LedgerError(f"candidate: missing required field {field!r}")
    if cand["lane"] not in LANES:
        raise LedgerError(
            f"candidate: unknown lane {cand['lane']!r} (allowed: {sorted(LANES)})"
        )
    if cand["format"] not in FORMATS:
        raise LedgerError(f"candidate: unknown format {cand['format']!r}")
    if cand["hook_archetype"] not in HOOK_ARCHETYPES:
        raise LedgerError(
            f"candidate: unknown hook_archetype {cand['hook_archetype']!r} "
            f"(allowed: {sorted(HOOK_ARCHETYPES)})"
        )
    if cand["cta_type"] not in CTA_TYPES:
        raise LedgerError(
            f"candidate: unknown cta_type {cand['cta_type']!r} "
            f"(allowed: {sorted(CTA_TYPES)})"
        )
    if not isinstance(cand.get("entities", []), list):
        raise LedgerError("candidate: entities must be a list of slugs")
    if cand["format"] == "reel":
        if cand.get("visual_device") not in VISUAL_DEVICES:
            raise LedgerError(
                f"candidate: a reel needs a visual_device from "
                f"{sorted(VISUAL_DEVICES)}, got {cand.get('visual_device')!r}"
            )
    cand["_date"] = _parse_date(cand["date"], "candidate")


def check(cand: dict, rows: list) -> list:
    """Return a list of human-readable violations (empty = clean)."""
    violations = []
    cdate = cand["_date"]
    lane = cand["lane"]

    # Unique id.
    if any(r["id"] == cand["id"] for r in rows):
        violations.append(f"id {cand['id']!r} already exists in the ledger")

    # Declared derivative? Verify the claim before honoring it.
    recut_ok = False
    if cand.get("recut_of"):
        src = next((r for r in rows if r["id"] == cand["recut_of"]), None)
        if src is None:
            violations.append(
                f"recut_of names {cand['recut_of']!r} but no such ledger row exists"
            )
        elif src["format"] == cand["format"]:
            violations.append(
                f"recut_of {cand['recut_of']!r} is the same format "
                f"({cand['format']}) -- a re-cut must cross formats"
            )
        else:
            recut_ok = True

    # 1. Signal entity window.
    if lane == "signal":
        for entity in cand.get("entities", []):
            for r in rows:
                if r["lane"] != "signal":
                    continue
                if entity in (r.get("entities") or []) and (
                    0 <= (cdate - r["_date"]).days <= ENTITY_WINDOW_DAYS
                ):
                    violations.append(
                        f"entity {entity!r} ran in {r['id']} on {r['date']} "
                        f"({(cdate - r['_date']).days}d ago; window "
                        f"{ENTITY_WINDOW_DAYS}d)"
                    )

    # 2. angle_key window per lane.
    if not recut_ok:
        same_angle = [
            r for r in rows
            if r["lane"] == lane and r["angle_key"] == cand["angle_key"]
        ]
        if lane == "news":
            for r in same_angle:
                update_of = cand.get("update_of")
                if update_of and update_of in (r["id"], r["angle_key"]):
                    continue  # a declared, verifiable update
                violations.append(
                    f"news angle {cand['angle_key']!r} already ran as {r['id']} "
                    f"on {r['date']} -- news runs once ever unless the candidate "
                    f"declares update_of pointing at it"
                )
        else:
            window = ANGLE_WINDOW_DAYS[lane]
            for r in same_angle:
                age = (cdate - r["_date"]).days
                if 0 <= age <= window:
                    violations.append(
                        f"angle {cand['angle_key']!r} ran in {r['id']} on "
                        f"{r['date']} ({age}d ago; window {window}d)"
                    )
        if cand.get("update_of") and lane == "news":
            known = {r["id"] for r in rows} | {r["angle_key"] for r in rows}
            if cand["update_of"] not in known:
                violations.append(
                    f"update_of names {cand['update_of']!r} but no ledger row "
                    f"matches it"
                )

    # 3. key_line: exact (normalized) match is banned forever, any lane.
    if cand.get("key_line") and not recut_ok:
        norm = _norm_line(cand["key_line"])
        for r in rows:
            if r.get("key_line") and _norm_line(r["key_line"]) == norm:
                violations.append(
                    f"key_line is an exact repeat of {r['id']} ({r['date']}) -- "
                    f"exact lines never re-run"
                )

    # 4. hook_archetype: never on consecutive posts.
    dated = sorted(rows, key=lambda r: (r["_date"], r["id"]))
    last_hooked = next(
        (r for r in reversed(dated) if r.get("hook_archetype")), None
    )
    if last_hooked and last_hooked["hook_archetype"] == cand["hook_archetype"]:
        violations.append(
            f"hook_archetype {cand['hook_archetype']!r} was also the most "
            f"recent post's hook ({last_hooked['id']}) -- rotate it"
        )

    # 5. cta_type: not more than CTA_MAX_CONSECUTIVE_DAYS days running.
    prior_dates = sorted({r["_date"] for r in rows if r["_date"] < cdate})
    recent = prior_dates[-CTA_MAX_CONSECUTIVE_DAYS:]
    if len(recent) == CTA_MAX_CONSECUTIVE_DAYS and all(
        any(
            r["_date"] == d and r.get("cta_type") == cand["cta_type"]
            for r in rows
        )
        for d in recent
    ):
        violations.append(
            f"cta_type {cand['cta_type']!r} already ran on the last "
            f"{CTA_MAX_CONSECUTIVE_DAYS} posting days "
            f"({', '.join(d.isoformat() for d in recent)}) -- vary it"
        )

    # 6. Same-day visual device between Reels.
    if cand["format"] == "reel" and cand.get("visual_device"):
        for r in rows:
            if (
                r["format"] == "reel"
                and r["_date"] == cdate
                and r.get("visual_device") == cand["visual_device"]
            ):
                violations.append(
                    f"visual_device {cand['visual_device']!r} already used by "
                    f"today's other reel ({r['id']}) -- two same-day reels must "
                    f"not share a motion device"
                )
    return violations


def _load_candidate(path: Path) -> dict:
    try:
        cand = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LedgerError(f"cannot read candidate {path}: {exc}")
    if not isinstance(cand, dict):
        raise LedgerError(f"candidate {path} must be a single JSON object")
    validate_candidate(cand)
    return cand


def append_row(cand: dict, ledger_path: Path) -> None:
    row = {
        "id": cand["id"],
        "date": cand["date"],
        "lane": cand["lane"],
        "format": cand["format"],
        "entities": cand.get("entities", []),
        "angle_key": cand["angle_key"],
        "hook_archetype": cand["hook_archetype"],
        "cta_type": cand["cta_type"],
        "visual_device": cand.get("visual_device"),
        "key_line": cand.get("key_line"),
        "update_of": cand.get("update_of"),
        "recut_of": cand.get("recut_of"),
        "status": cand.get("status", "queued"),
        "ig_post_id": cand.get("ig_post_id"),
        "permalink": cand.get("permalink"),
    }
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("check", "append"))
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args(argv)

    try:
        rows = load_ledger(args.ledger)
        cand = _load_candidate(args.candidate)
        violations = check(cand, rows)
    except LedgerError as exc:
        print(f"REPETITION GATE ERROR (fail closed): {exc}", file=sys.stderr)
        return EXIT_FAIL

    if violations:
        print(f"REPETITION GATE: FAIL ({len(violations)})", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return EXIT_FAIL

    if args.command == "append":
        append_row(cand, args.ledger)
        print(f"REPETITION GATE: PASS -- appended {cand['id']} to {args.ledger}")
    else:
        print(f"REPETITION GATE: PASS -- {cand['id']}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
