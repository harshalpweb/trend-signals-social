"""Tests for the weekly-routine output-count guard (CTO ruling 2026-08-26).

The property under test: a headless `claude -p` run that exits 0 must NOT be
treated as success unless it actually queued new content and committed it --
mirroring the same "a green run must mean real work happened" discipline
already enforced on the publish side (test_incident_throttle.py). No network,
no real subprocess calls to claude.exe -- _run_claude and _git_head are
monkeypatched directly, matching this repo's existing test style.
"""
import run_weekly_routine as rwr


def _seed_queue(tmp_path, n, monkeypatch):
    queue_dir = tmp_path / "content" / "queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(rwr, "QUEUE_DIR", queue_dir)
    # TEMPLATE.json always exists and must never count as a real queued post.
    (queue_dir / "TEMPLATE.json").write_text("{}", encoding="utf-8")
    for i in range(n):
        (queue_dir / f"post-{i}.json").write_text("{}", encoding="utf-8")
    return queue_dir


def test_claude_nonzero_exit_fails_before_checking_output(tmp_path, monkeypatch):
    _seed_queue(tmp_path, 0, monkeypatch)
    monkeypatch.setattr(rwr, "_git_head", lambda: "abc123")
    monkeypatch.setattr(rwr, "_run_claude", lambda: 1)
    assert rwr.main() == rwr.EXIT_CLAUDE_FAILED


def test_zero_new_posts_fails_even_though_claude_exited_zero(tmp_path, monkeypatch):
    """The exact defect this guard exists to catch: the 2026-08-23 shape --
    claude.exe completes cleanly, TEMPLATE.json is still the only file, no
    new post was ever queued."""
    _seed_queue(tmp_path, 0, monkeypatch)
    monkeypatch.setattr(rwr, "_git_head", lambda: "abc123")
    monkeypatch.setattr(rwr, "_run_claude", lambda: 0)
    assert rwr.main() == rwr.EXIT_ZERO_OUTPUT


def test_new_posts_but_no_new_commit_fails(tmp_path, monkeypatch):
    queue_dir = _seed_queue(tmp_path, 0, monkeypatch)
    heads = iter(["abc123", "abc123"])  # HEAD unchanged despite new files on disk

    def _run_claude():
        (queue_dir / "post-0.json").write_text("{}", encoding="utf-8")
        return 0

    monkeypatch.setattr(rwr, "_git_head", lambda: next(heads))
    monkeypatch.setattr(rwr, "_run_claude", _run_claude)
    assert rwr.main() == rwr.EXIT_UNCOMMITTED


def test_new_posts_and_new_commit_succeeds(tmp_path, monkeypatch):
    queue_dir = _seed_queue(tmp_path, 0, monkeypatch)
    heads = iter(["abc123", "def456"])

    def _run_claude():
        (queue_dir / "post-0.json").write_text("{}", encoding="utf-8")
        (queue_dir / "post-1.json").write_text("{}", encoding="utf-8")
        return 0

    monkeypatch.setattr(rwr, "_git_head", lambda: next(heads))
    monkeypatch.setattr(rwr, "_run_claude", _run_claude)
    assert rwr.main() == rwr.EXIT_OK


def test_partial_week_one_post_of_several_still_succeeds(tmp_path, monkeypatch):
    """A partial week from the routine's own documented per-post skip logic
    is a real success, not a failure -- this guard only catches TOTAL zero
    output, never enforces a specific target count."""
    queue_dir = _seed_queue(tmp_path, 0, monkeypatch)
    heads = iter(["abc123", "def456"])

    def _run_claude():
        (queue_dir / "post-0.json").write_text("{}", encoding="utf-8")
        return 0

    monkeypatch.setattr(rwr, "_git_head", lambda: next(heads))
    monkeypatch.setattr(rwr, "_run_claude", _run_claude)
    assert rwr.main() == rwr.EXIT_OK


def test_template_json_never_counts_as_a_queued_post(tmp_path, monkeypatch):
    """Regression guard for the counting logic itself: a repo with only
    TEMPLATE.json present (the real, permanent state of an empty queue)
    must count as zero queued posts, not one."""
    _seed_queue(tmp_path, 0, monkeypatch)
    assert rwr._count_queued_posts() == 0


def test_not_a_git_repo_fails_with_config_exit_before_running_claude(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(rwr, "_git_head", lambda: None)
    monkeypatch.setattr(rwr, "_run_claude", lambda: called.append(True) or 0)
    assert rwr.main() == rwr.EXIT_CONFIG
    assert called == [], "claude.exe must never be invoked if the repo state can't be verified"
