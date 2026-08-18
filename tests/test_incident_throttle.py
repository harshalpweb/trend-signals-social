"""Tests for the hourly-alert incident throttle. No network, no credentials.

The property under test is "honest quiet": a standing incident must stop
emailing the founder every hour, WITHOUT ever hiding an hour in which a post
was actually lost. So each test pins one of the four branches:

    first detection            -> red (exit 2), record written
    repeat, nothing due        -> green (exit 0), counter still increments
    repeat, something due      -> red (exit 2)
    success with open incident -> green, record deleted, RECOVERED printed

plus the input that decides the "something due" branch: publish_due_posts.py
--count-due.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import check_token
import ig_common
import publish_due_posts
from ig_common import GraphAPIError

FAKE_TOKEN = "IGAAFAKEtoken0000000000000000000000000000000000SECRETVALUE"
FAKE_USER_ID = "27870001472663258"


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("IG_ACCESS_TOKEN", FAKE_TOKEN)
    monkeypatch.setenv("IG_USER_ID", FAKE_USER_ID)
    monkeypatch.delenv("IG_AUTH_MODE", raising=False)
    monkeypatch.setattr(ig_common, "_SECRETS", [], raising=False)
    yield


def _blocked(*_args, **_kwargs):
    """The live production failure: OAuthException code 200."""
    raise GraphAPIError(
        "OAuthException code=200: API access blocked.",
        kind="api",
        code=200,
        err_type="OAuthException",
        status_code=400,
    )


def _live(*_args, **_kwargs):
    return {"id": FAKE_USER_ID, "username": "trendradar.in"}


def _run(monkeypatch, probe, incident: Path, due: str = "0") -> int:
    monkeypatch.setattr(check_token, "api_get", probe)
    return check_token.main(
        ["--incident-file", str(incident), "--due-count", due]
    )


# --------------------------------------------------------------------------
# check_token.py --incident-file / --due-count
# --------------------------------------------------------------------------


def test_first_detection_writes_record_and_fails(tmp_path, monkeypatch, capsys):
    incident = tmp_path / "INCIDENT.json"

    assert _run(monkeypatch, _blocked, incident) == check_token.EXIT_OAUTH

    state = json.loads(incident.read_text(encoding="utf-8"))
    assert state["checks_failed"] == 1
    assert state["code"] == 200
    assert state["auth_mode"] == "instagram_login"
    assert "API access blocked" in state["message"]
    assert "app/account-level restriction" in state["hint"]
    assert state["first_seen_utc"] == state["last_seen_utc"]
    assert "INCIDENT OPENED" in capsys.readouterr().err


def test_repeat_detection_with_no_due_posts_stays_green_and_counts(
    tmp_path, monkeypatch, capsys
):
    incident = tmp_path / "INCIDENT.json"

    assert _run(monkeypatch, _blocked, incident) == check_token.EXIT_OAUTH
    first_seen = json.loads(incident.read_text(encoding="utf-8"))["first_seen_utc"]
    capsys.readouterr()

    for expected_count in (2, 3, 4):
        assert _run(monkeypatch, _blocked, incident, due="0") == check_token.EXIT_OK
        out = capsys.readouterr().out
        state = json.loads(incident.read_text(encoding="utf-8"))
        # Quiet, but not amnesiac: the record keeps counting and the run still
        # prints the failure line, so the log tells the whole truth.
        assert state["checks_failed"] == expected_count
        assert state["first_seen_utc"] == first_seen
        assert "incident ongoing since" in out
        assert "not failing the run" in out


def test_repeat_detection_with_due_posts_fails(tmp_path, monkeypatch, capsys):
    incident = tmp_path / "INCIDENT.json"
    assert _run(monkeypatch, _blocked, incident) == check_token.EXIT_OAUTH
    assert _run(monkeypatch, _blocked, incident, due="0") == check_token.EXIT_OK

    assert _run(monkeypatch, _blocked, incident, due="2") == check_token.EXIT_OAUTH
    err = capsys.readouterr().err
    assert "2 post(s) due" in err


def test_unparseable_due_count_fails_loudly(tmp_path, monkeypatch):
    # An empty/garbage $DUE means we do not know whether posts are due; the
    # safe reading is "yes", i.e. go red rather than risk a silent loss.
    incident = tmp_path / "INCIDENT.json"
    assert _run(monkeypatch, _blocked, incident) == check_token.EXIT_OAUTH
    assert _run(monkeypatch, _blocked, incident, due="") == check_token.EXIT_OAUTH
    assert _run(monkeypatch, _blocked, incident, due="oops") == check_token.EXIT_OAUTH


def test_corrupt_record_is_treated_as_first_detection(tmp_path, monkeypatch):
    incident = tmp_path / "INCIDENT.json"
    incident.write_text("{not json", encoding="utf-8")

    assert _run(monkeypatch, _blocked, incident, due="0") == check_token.EXIT_OAUTH
    assert json.loads(incident.read_text(encoding="utf-8"))["checks_failed"] == 1


def test_recovery_deletes_record_and_reports(tmp_path, monkeypatch, capsys):
    incident = tmp_path / "INCIDENT.json"
    assert _run(monkeypatch, _blocked, incident) == check_token.EXIT_OAUTH
    first_seen = json.loads(incident.read_text(encoding="utf-8"))["first_seen_utc"]
    capsys.readouterr()

    assert _run(monkeypatch, _live, incident) == check_token.EXIT_OK

    out = capsys.readouterr().out
    assert not incident.exists()
    assert "RECOVERED" in out
    assert first_seen in out


def test_success_without_open_incident_is_silent_about_recovery(
    tmp_path, monkeypatch, capsys
):
    incident = tmp_path / "INCIDENT.json"
    assert _run(monkeypatch, _live, incident) == check_token.EXIT_OK
    assert "RECOVERED" not in capsys.readouterr().out
    assert not incident.exists()


def test_no_flag_behaviour_is_unchanged(tmp_path, monkeypatch, capsys):
    # Job #1's contract: bare `python scripts/check_token.py` still always
    # exits 2 on an OAuthException and writes no incident file anywhere.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(check_token, "api_get", _blocked)
    assert check_token.main([]) == check_token.EXIT_OAUTH
    assert check_token.main([]) == check_token.EXIT_OAUTH
    assert list(tmp_path.iterdir()) == []
    assert "HINT: code 200" in capsys.readouterr().err


def test_incident_record_never_contains_the_token(tmp_path, monkeypatch):
    incident = tmp_path / "INCIDENT.json"

    def leaky(*_args, **_kwargs):
        ig_common.register_secret(FAKE_TOKEN)
        raise GraphAPIError(
            f"OAuthException code=190: bad call to /me?access_token={FAKE_TOKEN}",
            kind="api",
            code=190,
        )

    assert _run(monkeypatch, leaky, incident) == check_token.EXIT_OAUTH
    assert FAKE_TOKEN not in incident.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# publish_due_posts.py --count-due
# --------------------------------------------------------------------------


def _write_post(queue: Path, post_id: str, offset_hours: int, **overrides) -> None:
    scheduled = datetime.now(timezone.utc) + timedelta(hours=offset_hours)
    post = {
        "id": post_id,
        "type": "signal",
        "caption": "c",
        "slides": [f"content/queue/slides/{post_id}-1.png"],
        "scheduled_time_ist": scheduled.astimezone(
            timezone(timedelta(hours=5, minutes=30))
        ).isoformat(),
        "status": "pending",
        "needs_review": False,
    }
    post.update(overrides)
    (queue / f"{post_id}.json").write_text(json.dumps(post, indent=2), encoding="utf-8")


def test_count_due_counts_only_publishable_due_posts(tmp_path, monkeypatch, capsys):
    queue = tmp_path / "queue"
    queue.mkdir()
    _write_post(queue, "due-now", -1)
    _write_post(queue, "due-earlier", -48)
    _write_post(queue, "not-yet", +5)
    _write_post(queue, "already-posted", -3, status="posted")
    _write_post(queue, "held", -3, needs_review=True)
    (queue / "TEMPLATE.json").write_text('{"id": "TEMPLATE"}', encoding="utf-8")
    monkeypatch.setattr(publish_due_posts, "QUEUE_DIR", queue)

    assert publish_due_posts.main(["--count-due"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == "2"
    # "prints ONLY the integer": the needs_review skip line must not leak into
    # $DUE, or the shell would hand check_token.py a non-numeric value.
    assert captured.out.strip().isdigit()
    # No side effects: nothing moved, nothing rewritten.
    assert len(list(queue.glob("*.json"))) == 6


def test_count_due_counts_malformed_posts_as_due(tmp_path, monkeypatch, capsys):
    # A malformed queue file is work the publisher WILL act on (it fails it and
    # goes red), so it counts as due — the throttle must not stay green on it.
    queue = tmp_path / "queue"
    queue.mkdir()
    (queue / "broken.json").write_text("{oops", encoding="utf-8")
    _write_post(queue, "missing-fields", -1)
    bad = json.loads((queue / "missing-fields.json").read_text(encoding="utf-8"))
    bad.pop("caption")
    (queue / "missing-fields.json").write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(publish_due_posts, "QUEUE_DIR", queue)

    assert publish_due_posts.main(["--count-due"]) == 0
    assert capsys.readouterr().out.strip() == "2"


def test_count_due_on_empty_queue_prints_zero(tmp_path, monkeypatch, capsys):
    queue = tmp_path / "queue"
    queue.mkdir()
    monkeypatch.setattr(publish_due_posts, "QUEUE_DIR", queue)

    assert publish_due_posts.main(["--count-due"]) == 0
    assert capsys.readouterr().out.strip() == "0"


def test_count_due_needs_no_credentials(tmp_path, monkeypatch, capsys):
    # publish.yml runs --count-due in the token-check step; it must not require
    # IG_USER_ID/IG_ACCESS_TOKEN/GITHUB_REPOSITORY to be present.
    for name in ("IG_USER_ID", "IG_ACCESS_TOKEN", "GITHUB_REPOSITORY"):
        monkeypatch.delenv(name, raising=False)
    queue = tmp_path / "queue"
    queue.mkdir()
    monkeypatch.setattr(publish_due_posts, "QUEUE_DIR", queue)

    assert publish_due_posts.main(["--count-due"]) == 0
    assert capsys.readouterr().out.strip() == "0"


def test_publish_path_still_requires_credentials(monkeypatch):
    monkeypatch.setattr(publish_due_posts, "IG_USER_ID", "")
    monkeypatch.setattr(publish_due_posts, "ACCESS_TOKEN", "")
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)

    with pytest.raises(SystemExit) as excinfo:
        publish_due_posts.main([])
    assert "missing env var(s)" in str(excinfo.value)
