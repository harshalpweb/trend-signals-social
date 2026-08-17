"""Publish due posts from content/queue/ to Instagram as carousels.

Run hourly by .github/workflows/publish.yml. Pure stdlib + requests — no AI/Canva
involved here; content is produced separately (see README).
"""
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API_VERSION = "v21.0"
BASE = f"https://graph.instagram.com/{API_VERSION}"
MAX_ATTEMPTS = 3
POLL_INTERVAL_S = 3
POLL_TIMEOUT_S = 60

ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = ROOT / "content" / "queue"
POSTED_DIR = ROOT / "content" / "posted"
FAILED_DIR = ROOT / "content" / "failed"

IG_USER_ID = os.environ["IG_USER_ID"]
ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
RAW_BASE = f"https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/main"

REQUIRED_FIELDS = ["id", "type", "caption", "slides", "scheduled_time_ist", "status"]


class PostError(Exception):
    pass


def load_due_posts():
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
        if post["status"] != "pending":
            continue
        scheduled = datetime.fromisoformat(post["scheduled_time_ist"])
        if scheduled <= now:
            due.append((path, post, None))
    return due


def create_item_container(slide_path: str) -> str:
    image_url = f"{RAW_BASE}/{slide_path}"
    resp = requests.post(
        f"{BASE}/{IG_USER_ID}/media",
        data={"image_url": image_url, "is_carousel_item": "true", "access_token": ACCESS_TOKEN},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def wait_until_finished(container_id: str) -> None:
    deadline = time.time() + POLL_TIMEOUT_S
    while time.time() < deadline:
        resp = requests.get(
            f"{BASE}/{container_id}",
            params={"fields": "status_code", "access_token": ACCESS_TOKEN},
            timeout=30,
        )
        resp.raise_for_status()
        status = resp.json().get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise PostError(f"container {container_id} failed processing")
        time.sleep(POLL_INTERVAL_S)
    raise PostError(f"container {container_id} timed out waiting to finish")


def create_carousel_container(item_ids, caption: str) -> str:
    resp = requests.post(
        f"{BASE}/{IG_USER_ID}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(item_ids),
            "caption": caption,
            "access_token": ACCESS_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def publish_container(container_id: str) -> str:
    resp = requests.post(
        f"{BASE}/{IG_USER_ID}/media_publish",
        data={"creation_id": container_id, "access_token": ACCESS_TOKEN},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def publish_post(post: dict) -> str:
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
    (post_dir / f"{post['id']}.json").write_text(json.dumps(post, indent=2), encoding="utf-8")
    path.unlink(missing_ok=True)


def main() -> None:
    due = load_due_posts()
    if not due:
        print("No due posts.")
        return

    for path, post, precheck_error in due:
        print(f"Processing {post.get('id', path.name)}...")
        if precheck_error is not None:
            post["status"] = "failed"
            post["last_error"] = str(precheck_error)
            move_post(path, post, FAILED_DIR)
            print(f"  malformed -> failed: {precheck_error}")
            continue

        try:
            ig_post_id = publish_post(post)
        except Exception as e:  # noqa: BLE001 - deliberately broad; every failure mode retries/fails the same way
            post["attempts"] = post.get("attempts", 0) + 1
            post["last_error"] = str(e)
            if post["attempts"] >= MAX_ATTEMPTS:
                post["status"] = "failed"
                move_post(path, post, FAILED_DIR)
                print(f"  failed permanently after {post['attempts']} attempts: {e}")
            else:
                path.write_text(json.dumps(post, indent=2), encoding="utf-8")
                print(f"  attempt {post['attempts']} failed, will retry next run: {e}")
        else:
            post["status"] = "posted"
            post["ig_post_id"] = ig_post_id
            post["posted_at"] = datetime.now(timezone.utc).isoformat()
            move_post(path, post, POSTED_DIR)
            print(f"  posted: {ig_post_id}")


if __name__ == "__main__":
    main()
