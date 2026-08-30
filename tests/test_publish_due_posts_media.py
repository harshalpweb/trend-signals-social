import publish_due_posts as publisher


def test_publish_post_routes_video_to_reel(monkeypatch):
    captured = {}

    def fake_publish(video_path, caption):
        captured.update(video_path=video_path, caption=caption)
        return "reel-media-id"

    monkeypatch.setattr(publisher, "publish_reel", fake_publish)
    result = publisher.publish_post(
        {"video": "content/queue/video/demo.mp4", "caption": "Demo caption"}
    )
    assert result == "reel-media-id"
    assert captured == {
        "video_path": "content/queue/video/demo.mp4",
        "caption": "Demo caption",
    }


def test_publish_reel_creates_processes_and_publishes(monkeypatch):
    posts = []
    monkeypatch.setattr(publisher, "RAW_BASE", "https://raw.example/repo/main")
    monkeypatch.setattr(publisher, "IG_USER_ID", "ig-user")
    monkeypatch.setattr(publisher, "ACCESS_TOKEN", "token")
    monkeypatch.setattr(publisher, "BASE", "https://graph.example/v1")
    monkeypatch.setattr(
        publisher,
        "api_post",
        lambda path, token, data, base: posts.append((path, token, data, base)) or {"id": "container-1"},
    )
    monkeypatch.setattr(publisher, "wait_until_finished", lambda container_id: None)
    monkeypatch.setattr(publisher, "publish_container", lambda container_id: "published-1")

    result = publisher.publish_reel("content/queue/video/demo.mp4", "Caption")

    assert result == "published-1"
    assert posts == [
        (
            "ig-user/media",
            "token",
            {
                "media_type": "REELS",
                "video_url": "https://raw.example/repo/main/content/queue/video/demo.mp4",
                "caption": "Caption",
                "share_to_feed": "true",
            },
            "https://graph.example/v1",
        )
    ]
