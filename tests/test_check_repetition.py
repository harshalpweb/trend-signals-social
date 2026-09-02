# -*- coding: utf-8 -*-
"""Tests for the fail-closed anti-repetition gate. No network, no credentials.

The property under test is "auditable no-repeat": every window in the
2026-08-29 niche consult's section 2.4 must actually block, the declared
escape hatches (news update_of, cross-format recut_of) must only open when
their claim is verifiable in the ledger, and anything unreadable or
unclassifiable must FAIL, never slip through.
"""
import json
from pathlib import Path

import pytest

import check_repetition as cr


def _row(**overrides) -> dict:
    row = {
        "id": "2026-09-01-seller_wisdom-05",
        "date": "2026-09-01",
        "lane": "seller_wisdom",
        "format": "carousel",
        "entities": [],
        "angle_key": "wisdom:packaging-is-the-brand",
        "hook_archetype": None,
        "cta_type": None,
        "visual_device": None,
        "key_line": None,
        "update_of": None,
        "recut_of": None,
        "status": "posted",
    }
    row.update(overrides)
    return row


def _cand(**overrides) -> dict:
    cand = {
        "id": "2026-09-03-seller_wisdom-06",
        "date": "2026-09-03",
        "lane": "seller_wisdom",
        "format": "carousel",
        "entities": [],
        "angle_key": "wisdom:cod-cash-reality",
        "hook_archetype": "stake_statement",
        "cta_type": "comment",
    }
    cand.update(overrides)
    return cand


def _write_ledger(tmp_path: Path, rows) -> Path:
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
    )
    return ledger


def _run(tmp_path, rows, cand, command="check") -> int:
    ledger = _write_ledger(tmp_path, rows)
    cand_path = tmp_path / "candidate.json"
    cand_path.write_text(json.dumps(cand), encoding="utf-8")
    return cr.main([command, str(cand_path), "--ledger", str(ledger)])


# --------------------------------------------------------------------------
# Fail-closed basics
# --------------------------------------------------------------------------


def test_missing_ledger_fails_closed(tmp_path, capsys):
    cand_path = tmp_path / "candidate.json"
    cand_path.write_text(json.dumps(_cand()), encoding="utf-8")
    assert (
        cr.main(["check", str(cand_path), "--ledger", str(tmp_path / "nope.jsonl")])
        == cr.EXIT_FAIL
    )
    assert "fail closed" in capsys.readouterr().err


def test_corrupt_ledger_line_fails_closed(tmp_path, capsys):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps(_row()) + "\n{oops\n", encoding="utf-8")
    cand_path = tmp_path / "candidate.json"
    cand_path.write_text(json.dumps(_cand()), encoding="utf-8")
    assert cr.main(["check", str(cand_path), "--ledger", str(ledger)]) == cr.EXIT_FAIL
    assert "line 2" in capsys.readouterr().err


@pytest.mark.parametrize(
    "field,value",
    [
        ("lane", "motivation"),
        ("format", "story"),
        ("hook_archetype", "clickbait"),
        ("cta_type", "smash-that-like"),
        ("hook_archetype", None),
        ("angle_key", ""),
    ],
)
def test_unknown_or_missing_vocabulary_fails(tmp_path, field, value):
    assert _run(tmp_path, [_row()], _cand(**{field: value})) == cr.EXIT_FAIL


def test_reel_without_visual_device_fails(tmp_path):
    cand = _cand(format="reel")
    assert _run(tmp_path, [_row()], cand) == cr.EXIT_FAIL


def test_duplicate_id_fails(tmp_path):
    assert (
        _run(tmp_path, [_row()], _cand(id=_row()["id"], angle_key="wisdom:x"))
        == cr.EXIT_FAIL
    )


def test_clean_candidate_passes(tmp_path, capsys):
    assert _run(tmp_path, [_row()], _cand()) == cr.EXIT_OK
    assert "PASS" in capsys.readouterr().out


# --------------------------------------------------------------------------
# Windows
# --------------------------------------------------------------------------


def test_signal_entity_blocked_inside_14_days(tmp_path):
    prior = _row(
        id="2026-08-25-signal-01",
        date="2026-08-25",
        lane="signal",
        angle_key="signal:mixer-grinder:rising",
        entities=["mixer-grinder"],
    )
    cand = _cand(
        lane="signal",
        angle_key="signal:mixer-grinder:second-family-agrees",
        entities=["mixer-grinder"],
        date="2026-09-03",
    )
    assert _run(tmp_path, [prior], cand) == cr.EXIT_FAIL


def test_signal_entity_allowed_after_window(tmp_path):
    prior = _row(
        id="2026-08-10-signal-01",
        date="2026-08-10",
        lane="signal",
        angle_key="signal:mixer-grinder:rising",
        entities=["mixer-grinder"],
    )
    cand = _cand(
        lane="signal",
        angle_key="signal:mixer-grinder:rising-again",
        entities=["mixer-grinder"],
        date="2026-09-03",
    )
    assert _run(tmp_path, [prior], cand) == cr.EXIT_OK


def test_wisdom_angle_blocked_inside_60_days(tmp_path):
    cand = _cand(angle_key=_row()["angle_key"], date="2026-10-15")
    assert _run(tmp_path, [_row()], cand) == cr.EXIT_FAIL


def test_wisdom_angle_allowed_after_60_days(tmp_path):
    cand = _cand(angle_key=_row()["angle_key"], date="2026-11-15")
    assert _run(tmp_path, [_row()], cand) == cr.EXIT_OK


def test_exact_key_line_blocked_forever_across_lanes(tmp_path):
    prior = _row(key_line="Depth wins searches. Breadth wins nothing on its own.")
    cand = _cand(
        lane="quote_card",
        angle_key="quote:new-angle",
        date="2027-08-01",
        key_line="depth wins searches breadth wins nothing on its own",
    )
    assert _run(tmp_path, [prior], cand) == cr.EXIT_FAIL


def test_news_angle_once_ever_without_update_of(tmp_path):
    prior = _row(
        id="2026-08-20-news-01",
        date="2026-08-20",
        lane="news",
        angle_key="news:gst-rate-change-2026-09",
    )
    cand = _cand(
        lane="news", angle_key="news:gst-rate-change-2026-09", date="2027-06-01"
    )
    assert _run(tmp_path, [prior], cand) == cr.EXIT_FAIL


def test_news_update_of_opens_the_gate_only_when_target_exists(tmp_path):
    prior = _row(
        id="2026-08-20-news-01",
        date="2026-08-20",
        lane="news",
        angle_key="news:gst-rate-change-2026-09",
    )
    ok = _cand(
        lane="news",
        angle_key="news:gst-rate-change-2026-09",
        update_of="2026-08-20-news-01",
    )
    assert _run(tmp_path, [prior], ok) == cr.EXIT_OK

    bogus = _cand(
        id="2026-09-04-news-02",
        lane="news",
        angle_key="news:gst-rate-change-2026-09",
        update_of="2026-01-01-news-nonexistent",
    )
    assert _run(tmp_path, [prior], bogus) == cr.EXIT_FAIL


def test_recut_of_bypasses_angle_window_only_across_formats(tmp_path):
    prior = _row(
        id="2026-09-01-seller_playbook-04",
        lane="seller_playbook",
        angle_key="playbook:weekly-money-hour",
    )
    recut = _cand(
        lane="seller_playbook",
        format="reel",
        visual_device="cost_counter",
        angle_key="playbook:weekly-money-hour",
        recut_of="2026-09-01-seller_playbook-04",
    )
    assert _run(tmp_path, [prior], recut) == cr.EXIT_OK

    same_format = _cand(
        id="2026-09-05-seller_playbook-05",
        lane="seller_playbook",
        angle_key="playbook:weekly-money-hour",
        recut_of="2026-09-01-seller_playbook-04",
    )
    assert _run(tmp_path, [prior], same_format) == cr.EXIT_FAIL


def test_hook_archetype_blocked_on_consecutive_posts(tmp_path):
    prior = _row(hook_archetype="stake_statement")
    assert (
        _run(tmp_path, [prior], _cand(hook_archetype="stake_statement"))
        == cr.EXIT_FAIL
    )
    assert (
        _run(tmp_path, [prior], _cand(hook_archetype="count_promise"))
        == cr.EXIT_OK
    )


def test_cta_blocked_on_third_consecutive_day(tmp_path):
    rows = [
        _row(id="a", date="2026-09-01", cta_type="save"),
        _row(id="b", date="2026-09-02", cta_type="save",
             angle_key="wisdom:other-1"),
    ]
    assert (
        _run(tmp_path, rows, _cand(date="2026-09-03", cta_type="save"))
        == cr.EXIT_FAIL
    )
    assert (
        _run(tmp_path, rows, _cand(date="2026-09-03", cta_type="comment"))
        == cr.EXIT_OK
    )


def test_same_day_reels_may_not_share_visual_device(tmp_path):
    prior = _row(
        id="2026-09-03-reel-a",
        date="2026-09-03",
        format="reel",
        visual_device="receipt_print",
        angle_key="wisdom:reel-a",
    )
    clash = _cand(
        format="reel",
        visual_device="receipt_print",
        date="2026-09-03",
        angle_key="wisdom:reel-b",
    )
    ok = _cand(
        format="reel",
        visual_device="type_cut",
        date="2026-09-03",
        angle_key="wisdom:reel-b",
    )
    assert _run(tmp_path, [prior], clash) == cr.EXIT_FAIL
    assert _run(tmp_path, [prior], ok) == cr.EXIT_OK


# --------------------------------------------------------------------------
# Backfill tolerance + append
# --------------------------------------------------------------------------


def test_null_hook_and_cta_in_history_are_tolerated(tmp_path):
    # Backfilled rows predate the taxonomies; they must not crash the gate
    # or trigger the consecutive-hook rule.
    assert _run(tmp_path, [_row(hook_archetype=None, cta_type=None)], _cand()) == cr.EXIT_OK


def test_append_writes_exactly_one_valid_row(tmp_path):
    ledger = _write_ledger(tmp_path, [_row()])
    cand_path = tmp_path / "candidate.json"
    cand_path.write_text(json.dumps(_cand()), encoding="utf-8")

    assert cr.main(["append", str(cand_path), "--ledger", str(ledger)]) == cr.EXIT_OK

    lines = ledger.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    written = json.loads(lines[1])
    assert written["id"] == _cand()["id"]
    assert written["status"] == "queued"
    assert "_date" not in written


def test_append_refuses_on_violation(tmp_path):
    ledger = _write_ledger(tmp_path, [_row()])
    cand_path = tmp_path / "candidate.json"
    cand_path.write_text(
        json.dumps(_cand(angle_key=_row()["angle_key"], date="2026-09-03")),
        encoding="utf-8",
    )
    assert cr.main(["append", str(cand_path), "--ledger", str(ledger)]) == cr.EXIT_FAIL
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 1


def test_real_backfilled_ledger_loads_and_gates(tmp_path):
    # The committed ledger itself must parse, and a candidate repeating a
    # recently-posted playbook angle must be caught against it.
    real = cr.DEFAULT_LEDGER
    if not real.exists():
        pytest.skip("repo ledger not present")
    rows = cr.load_ledger(real)
    assert len(rows) >= 20
    cand = _cand(
        lane="seller_playbook",
        angle_key="playbook:return-cost-math",
        date="2026-09-03",
    )
    cand_path = tmp_path / "candidate.json"
    cand_path.write_text(json.dumps(cand), encoding="utf-8")
    assert cr.main(["check", str(cand_path), "--ledger", str(real)]) == cr.EXIT_FAIL
