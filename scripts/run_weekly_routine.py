"""Output-count guard around the headless instagram-weekly-routine run.

Why this exists (CTO ruling 2026-08-26, same failure class publish.yml
already fixed once): `claude -p "<run the weekly routine>"` exits 0 whenever
the CLI itself completes cleanly, regardless of whether the routine actually
queued any content. The routine's own failure-handling section says "if any
single post fails after retries, skip only that post and continue" -- which
is correct behavior for a partial week, but means a run that skips EVERY
post (e.g. because the Canva MCP tool allowlist is wrong again, as it was on
2026-08-23) still exits 0 and reports LastTaskResult: 0 in Task Scheduler.
That is indistinguishable, from the outside, from a healthy week.

This script does not replace the routine -- it wraps the same `claude -p`
invocation the Scheduled Task already runs, and adds exactly one check
`claude -p` cannot do about itself: did anything actually change on disk and
in git as a result. It intentionally does NOT require the full week's worth
of posts (posts_per_week from config.yaml) -- a partial week from documented
per-post skip logic is a real success, not a failure. It only catches the
specific, previously-observed failure mode: the run produced NOTHING.

Exit codes:
  0  claude.exe exited 0 AND queued >=1 new post AND made a new git commit
  1  claude.exe itself exited non-zero
  2  claude.exe exited 0 but queued ZERO new posts -- the exact defect this
     guard exists to catch (a "successful" run that did nothing)
  3  claude.exe exited 0 and queued posts, but made no new git commit --
     content/queue/ changes are uncommitted, so the hourly publish workflow
     (which only sees committed state) will never find them
  4  config/environment problem (claude.exe not found, not a git repo, etc.)

Usage: `py -3.12 scripts/run_weekly_routine.py` from the repo root. Since
2026-08-28 this IS what the Scheduled Task's Action invokes (re-registration
executed under explicit founder authorization, recorded in income-engine/
docs/consults/2026-08-28-group-cto-instagram-cadence-execution.md) -- the
guard is live on every scheduled run, not just manual ones.

Note (every-2-days cadence): a normal scheduled run always covers >=1
posting day (every consecutive-day pair in config.yaml's schedule contains
at least one posting day, and a dry signal slot still ships a no_signal
post), so the >=1-new-post bar remains correct. A *manual* re-run mid-cycle
whose 2-day horizon is already fully covered by surviving queue entries can
legitimately exit 2 -- check the queue before treating that as a failure.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = REPO_ROOT / "content" / "queue"
CLAUDE_EXE = r"C:\Users\2026\.local\bin\claude.exe"

# CANONICAL PROMPT (since 2026-08-28): the live Scheduled Task's Action now
# invokes THIS script (see scripts/register_instagram_task.ps1), so this is
# the single source of truth for the headless prompt -- the old
# three-copies-kept-in-sync arrangement (task Action / this file / register
# script) is gone; the register script no longer embeds its own copy.
# Horizon changed from "this week's posts" to "the next 2 days" per the
# founder's 2026-08-28 cadence decision (income-engine/docs/consults/
# 2026-08-28-group-cto-instagram-cadence-execution.md).
CLAUDE_PROMPT = (
    "Run the instagram-weekly-routine skill (see "
    ".claude/skills/instagram-weekly-routine/SKILL.md in this repo) to "
    "generate and queue TrendRadar Instagram posts for the NEXT 2 DAYS "
    "only, per instagram-growth/config.yaml's cadence.schedule. Follow "
    "that skill file exactly -- it documents the full sequence: "
    "instagram-signals "
    "(reads C:\\Users\\2026\\Documents\\income-engine\\trend_predictor "
    "read-only, and applies its MANDATORY family-aware freshness gate and "
    "freeze-detection rules) -> instagram-caption -> instagram-carousel "
    "(Canva MCP, locked master template DAHSjFtuvnU) -> assemble queue "
    "JSON -> git commit and push. A signal slot with zero gate-passing, "
    "non-repeating entities ships as a no_signal post per the skill -- "
    "never a stretched or stale claim, and never a silent skip. Do not "
    "publish anything directly -- that is handled "
    "separately by this repo's own hourly GitHub Actions workflow. If any "
    "single post fails after retries, skip only that post (per the skill's "
    "failure-handling section) and continue with the rest of the run "
    "rather than aborting the whole run."
)
CLAUDE_ARGS = [
    CLAUDE_EXE,
    "-p", CLAUDE_PROMPT,
    "--permission-mode", "acceptEdits",
    "--allowed-tools", "Bash", "Read", "Write", "Edit", "Glob", "Grep", "Skill",
    "mcp__plugin_canva_canva__*", "mcp__claude_ai_Canva__*",
    "--add-dir", r"C:\Users\2026\Documents\income-engine\trend_predictor",
]

EXIT_OK = 0
EXIT_CLAUDE_FAILED = 1
EXIT_ZERO_OUTPUT = 2
EXIT_UNCOMMITTED = 3
EXIT_CONFIG = 4


def _count_queued_posts() -> int:
    """Number of real post JSON files in content/queue/ (excludes the
    committed TEMPLATE.json, which is never a real queued post)."""
    if not QUEUE_DIR.is_dir():
        return 0
    return sum(
        1 for p in QUEUE_DIR.glob("*.json") if p.name != "TEMPLATE.json"
    )


def _git_head() -> str | None:
    """Current HEAD commit hash, or None if this isn't a readable git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    return result.stdout.strip()


def _run_claude() -> int:
    """Invoke the same headless claude -p command the Scheduled Task runs.
    Returns claude.exe's own exit code."""
    result = subprocess.run(CLAUDE_ARGS, cwd=REPO_ROOT)
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    # argv accepted for symmetry with this repo's other scripts' main(argv=None)
    # convention (called directly from tests); this script takes no arguments.
    del argv

    before_head = _git_head()
    if before_head is None:
        print(f"FAIL: {REPO_ROOT} is not a readable git repository", file=sys.stderr)
        return EXIT_CONFIG
    before_count = _count_queued_posts()

    claude_exit = _run_claude()
    if claude_exit != 0:
        print(f"FAIL: claude.exe exited {claude_exit}", file=sys.stderr)
        return EXIT_CLAUDE_FAILED

    after_count = _count_queued_posts()
    after_head = _git_head()
    new_posts = after_count - before_count
    new_commit = after_head is not None and after_head != before_head

    print(
        f"claude.exe exited 0. Queued posts before/after: "
        f"{before_count}/{after_count} (new: {new_posts}). "
        f"Git HEAD before/after: {before_head}/{after_head} "
        f"(new commit: {new_commit})"
    )

    if new_posts <= 0:
        print(
            "FAIL: weekly routine completed but queued ZERO new posts -- "
            "a run that produces nothing is not a success (same failure "
            "class as the 2026-08-23 run). Check the Canva MCP tool "
            "allowlist and this run's own transcript for what every post "
            "actually failed on.",
            file=sys.stderr,
        )
        return EXIT_ZERO_OUTPUT

    if not new_commit:
        print(
            "FAIL: weekly routine queued new post file(s) but made no new "
            "git commit -- content/queue/ has uncommitted changes, so the "
            "hourly publish workflow (which only sees committed state) "
            "will never see them. The routine's own git-commit-and-push "
            "step did not run or did not complete.",
            file=sys.stderr,
        )
        return EXIT_UNCOMMITTED

    print(f"OK: queued {new_posts} new post(s), committed {before_head} -> {after_head}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
