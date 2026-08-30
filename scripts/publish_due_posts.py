"""Publish due posts from content/queue/ to Instagram as carousels.

Run hourly by .github/workflows/publish.yml. Pure stdlib + requests — no AI/Canva
involved here; content is produced separately (see README).

Exit code: 0 only if every due post published. If ANY due post failed — malformed,
retry-pending, or permanently failed — the script still processes every remaining
post and still writes all state files, then exits 1 at the very end so the
workflow run goes red. A failed post must never be a green run.

Every Graph call goes through scripts/ig_common.py: token in an Authorization
header (never a query string) and every error string redacted, because
`last_error` is printed AND committed to git by publish.yml's `if: always()`
step — a token in an HTTPError message would be published to the repo.

`--count-due` prints just the number of currently-due posts and exits 0, doing
nothing else: no Graph call, no file written, no credentials required. It is the
input to check_token.py's `--due-count` incident throttle (see publish.yml), so
it must stay side-effect-free and must use exactly the same due logic as a real
run — otherwise the throttle would be deciding on a different reality than the
publisher acts on.
"""
import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import ig_common
from ig_common import api_get, api_post, graph_base, redact

MAX_ATTEMPTS = 3
POLL_INTERVAL_S = 3
POLL_TIMEOUT_S = 60

ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = ROOT / "content" / "queue"
POSTED_DIR = ROOT / "content" / "posted"
FAILED_DIR = ROOT / "content" / "failed"

# Read leniently at import time so `--count-due` (and the tests) work with no
# credentials in the environment; the publish path calls require_env() first and
# still dies loudly on anything missing.
IG_USER_ID = os.environ.get("IG_USER_ID", "")
ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
ig_common.register_secret(ACCESS_TOKEN)
BASE = graph_base()  # host follows IG_AUTH_MODE (instagram_login | facebook_login)
RAW_BASE = (
    f"https://raw.githubusercontent.com/"
    f"{os.environ.get('GITHUB_REPOSITORY', '')}/main"
)

REQUIRED_FIELDS = ["id", "type", "caption", "scheduled_time_ist", "status"]


class PostError(Exception):
    pass


def require_env() -> None:
    """Fail loudly before the first Graph call if publish config is missing."""
    missing = [
        name
        for name, value in (
            ("IG_USER_ID", IG_USER_ID),
            ("IG_ACCESS_TOKEN", ACCESS_TOKEN),
            ("GITHUB_REPOSITORY", os.environ.get("GITHUB_REPOSITORY", "")),
        )
        if not value
    ]
    if missing:
        raise SystemExit(f"FATAL: missing env var(s): {', '.join(missing)}")


def load_due_posts(verbose: bool = True):
    due = []
    now = datetime.now(timezone.utc)
    for path in sorted(QUEUE_DIR.glob("*.json")):
        if path.name == "TEMPLATE.json":
            continue
        try:
            post = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            due.append((path, {"id": path.stem, "status": "pending", "attempts": 0}, PostError(f"invalid json: {e}")))
            continue
        missing = [f for f in REQUIRED_FIELDS if f not in post]
        if missing:
            due.append((path, post, PostError(f"missing fields: {missing}")))
            continue
        if not post.get("slides") and not post.get("video"):
            due.append((path, post, PostError("missing media: provide slides or video")))
            continue
        if post["status"] != "pending":
            continue
        if post.get("needs_review"):
            # Held until a human clears the flag (edit the JSON, set needs_review to
            # false) — instagram-carousel's self-critique gate didn't fully pass on
            # this one, so it must not auto-publish on schedule.
            if verbose:
                print(f"  {post.get('id', path.name)} held: needs_review is true, skipping")
            continue
        scheduled = datetime.fromisoformat(post["scheduled_time_ist"])
        if scheduled <= now:
            due.append((path, post, None))
    return due


def create_item_container(slide_path: str) -> str:
    image_url = f"{RAW_BASE}/{slide_path}"
    payload = api_post(
        f"{IG_USER_ID}/media",
        ACCESS_TOKEN,
        data={"image_url": image_url, "is_carousel_item": "true"},
        base=BASE,
    )
    return payload["id"]


def wait_until_finished(container_id: str) -> None:
    deadline = time.time() + POLL_TIMEOUT_S
    while time.time() < deadline:
        payload = api_get(
            container_id, ACCESS_TOKEN, params={"fields": "status_code"}, base=BASE
        )
        status = payload.get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise PostError(f"container {container_id} failed processing")
        time.sleep(POLL_INTERVAL_S)
    raise PostError(f"container {container_id} timed out waiting to finish")


def create_carousel_container(item_ids, caption: str) -> str:
    payload = api_post(
        f"{IG_USER_ID}/media",
        ACCESS_TOKEN,
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(item_ids),
            "caption": caption,
        },
        base=BASE,
    )
    return payload["id"]


def publish_container(container_id: str) -> str:
    payload = api_post(
        f"{IG_USER_ID}/media_publish",
        ACCESS_TOKEN,
        data={"creation_id": container_id},
        base=BASE,
    )
    return payload["id"]


def publish_reel(video_path: str, caption: str) -> str:
    """Create, process and publish one Reel from a public repository video."""
    video_url = f"{RAW_BASE}/{video_path}"
    payload = api_post(
        f"{IG_USER_ID}/media",
        ACCESS_TOKEN,
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
        },
        base=BASE,
    )
    container_id = payload.get("id")
    if not container_id:
        raise PostError("reel container response had no id")
    wait_until_finished(container_id)
    return publish_container(container_id)


def publish_post(post: dict) -> str:
    if post.get("video"):
        return publish_reel(post["video"], post["caption"])
    if not post.get("slides"):
        raise PostError("no slides listed")
    item_ids = [create_item_container(slide) for slide in post["slides"]]
    for item_id in item_ids:
        wait_until_finished(item_id)
    carousel_id = create_carousel_container(item_ids, post["caption"])
    wait_until_finished(carousel_id)
    return publish_container(carousel_id)


def move_post(path: Path, post: dict, dest_dir: Path) -> None:
    post_dir = dest_dir / post["id"]
    post_dir.mkdir(parents=True, exist_ok=True)
    for slide in post.get("slides", []):
        slide_path = ROOT / slide
        if slide_path.exists():
            shutil.move(str(slide_path), str(post_dir / Path(slide).name))
    video_path = post.get("video")
    if video_path:
        source = ROOT / video_path
        if source.exists():
            shutil.move(str(source), str(post_dir / Path(video_path).name))
    (post_dir / f"{post['id']}.json").write_text(json.dumps(post, indent=2), encoding="utf-8")
    path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish due posts from content/queue/ to Instagram."
    )
    parser.add_argument(
        "--count-due",
        action="store_true",
        help="Print only the number of currently-due posts and exit 0. "
        "No Graph calls, no files touched, no credentials needed.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    # argv=None means "no arguments", NOT "read sys.argv" — main() is called
    # directly from the test suite, where sys.argv holds pytest's own flags.
    # The CLI entrypoint below passes sys.argv[1:] explicitly.
    args = build_parser().parse_args([] if argv is None else argv)
    if args.count_due:
        # Same due logic as a real run, silenced: a post the publisher would
        # skip must not be counted as due, or the incident throttle would fail
        # runs for work that was never going to happen.
        print(len(load_due_posts(verbose=False)))
        return 0

    require_env()
    due = load_due_posts()
    if not due:
        print("No due posts.")
        return 0

    # Collected, not raised: every due post is processed and every state file is
    # written before we decide the exit code.
    failures: list[str] = []

    for path, post, precheck_error in due:
        post_id = post.get("id", path.name)
        print(f"Processing {post_id}...")
        if precheck_error is not None:
            post["status"] = "failed"
            post["last_error"] = redact(precheck_error)
            move_post(path, post, FAILED_DIR)
            print(f"  malformed -> failed: {redact(precheck_error)}")
            failures.append(f"{post_id}: malformed ({redact(precheck_error)})")
            continue

        try:
            ig_post_id = publish_post(post)
        except Exception as e:  # noqa: BLE001 - deliberately broad; every failure mode retries/fails the same way
            # redact() is load-bearing: last_error is written to the queue JSON and
            # committed to the repo by publish.yml, so an un-redacted requests error
            # (which embeds the request URL) would publish the token.
            reason = redact(e)
            post["attempts"] = post.get("attempts", 0) + 1
            post["last_error"] = reason
            if post["attempts"] >= MAX_ATTEMPTS:
                post["status"] = "failed"
                move_post(path, post, FAILED_DIR)
                print(f"  failed permanently after {post['attempts']} attempts: {reason}")
                failures.append(f"{post_id}: failed permanently after {post['attempts']} attempts ({reason})")
            else:
                path.write_text(json.dumps(post, indent=2), encoding="utf-8")
                print(f"  attempt {post['attempts']} failed, will retry next run: {reason}")
                failures.append(f"{post_id}: attempt {post['attempts']} failed, retry pending ({reason})")
        else:
            post["status"] = "posted"
            post["ig_post_id"] = ig_post_id
            post["posted_at"] = datetime.now(timezone.utc).isoformat()
            move_post(path, post, POSTED_DIR)
            print(f"  posted: {ig_post_id}")

    if failures:
        print(f"\n{len(failures)} of {len(due)} due post(s) FAILED:", file=sys.stderr)
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        return 1

    print(f"\nAll {len(due)} due post(s) published.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001 - never let a traceback leak a token
        print(f"FATAL: {type(e).__name__}: {redact(e)}", file=sys.stderr)
        sys.exit(1)
