"""Tests for Instagram control functions (list_media, comments, insights, messaging, publish).

Offline only: all requests are mocked. Every function is tested for:
  1. Correct method + path + params/body
  2. Bearer token in Authorization header (never in URL/params)
  3. Error redaction (no token substring in error message)
"""
import json
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests

import ig_common

FAKE_TOKEN = "IGAAFAKEtoken0000000000000000000000000000000000SECRETVALUE"
FAKE_USER_ID = "17841440746293693"
FAKE_MEDIA_ID = "18000000000000001"
FAKE_COMMENT_ID = "18000000000000002"
FAKE_CONVERSATION_ID = "18000000000000003"
FAKE_RECIPIENT_ID = "100000000000001"

_NO_JSON = object()


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Clean environment and reset module state before each test."""
    for name in ("IG_AUTH_MODE", "IG_USER_ID_GRAPH", "GRAPH_API_VERSION"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(ig_common, "_SECRETS", [], raising=False)
    yield


class FakeResponse:
    def __init__(self, payload, status_code=200, text=None):
        self._payload = payload
        self.status_code = status_code
        self.text = text if text is not None else "<body>"

    def json(self):
        if self._payload is _NO_JSON:
            raise ValueError("no json")
        return self._payload


def fake_requests(responses, calls):
    """A stand-in for the `requests` module that records every call."""

    def _record(method):
        def _call(url, params=None, data=None, headers=None, timeout=None):
            calls.append(
                {
                    "method": method,
                    "url": url,
                    "params": params or {},
                    "data": data or {},
                    "headers": headers or {},
                    "timeout": timeout,
                }
            )
            result = responses.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        return _call

    return SimpleNamespace(
        get=_record("GET"),
        post=_record("POST"),
        delete=_record("DELETE"),
        RequestException=requests.RequestException,
    )


# ========================================================================
# list_media
# ========================================================================


def test_list_media_sends_bearer_header(monkeypatch):
    """list_media should send Bearer token in header, not params."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"data": [{"id": "m1", "caption": "hello"}]})], calls),
    )
    result = ig_common.list_media(FAKE_TOKEN)
    assert len(result) == 1
    assert result[0]["id"] == "m1"
    call = calls[0]
    assert call["method"] == "GET"
    assert "/me/media" in call["url"]
    assert call["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert "access_token" not in call["params"]
    assert FAKE_TOKEN not in call["url"]


def test_list_media_with_custom_limit_and_fields(monkeypatch):
    """list_media should pass limit and fields params."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"data": []})], calls),
    )
    ig_common.list_media(FAKE_TOKEN, limit=50, fields="id,permalink")
    call = calls[0]
    assert call["params"]["limit"] == 50
    assert call["params"]["fields"] == "id,permalink"


def test_list_media_error_is_redacted(monkeypatch):
    """Error messages from list_media should not contain the token."""
    calls = []
    leaky = requests.HTTPError(
        f"400 Client Error for url: https://graph.instagram.com/v21.0/me/media?access_token={FAKE_TOKEN}"
    )
    monkeypatch.setattr(ig_common, "requests", fake_requests([leaky], calls))
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.list_media(FAKE_TOKEN)
    assert FAKE_TOKEN not in str(exc.value)
    assert "<REDACTED>" in str(exc.value)


# ========================================================================
# list_comments
# ========================================================================


def test_list_comments_sends_correct_path_and_params(monkeypatch):
    """list_comments should GET /{media-id}/comments with fields param."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests(
            [FakeResponse({"data": [{"id": "c1", "text": "great post", "username": "user1"}]})],
            calls,
        ),
    )
    result = ig_common.list_comments(FAKE_MEDIA_ID, FAKE_TOKEN)
    assert len(result) == 1
    assert result[0]["text"] == "great post"
    call = calls[0]
    assert call["method"] == "GET"
    assert f"/{FAKE_MEDIA_ID}/comments" in call["url"]
    assert call["params"]["fields"] == "id,text,username,timestamp,like_count"
    assert call["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"


def test_list_comments_with_custom_fields(monkeypatch):
    """list_comments should accept custom fields."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"data": []})], calls),
    )
    ig_common.list_comments(FAKE_MEDIA_ID, FAKE_TOKEN, fields="id,text")
    call = calls[0]
    assert call["params"]["fields"] == "id,text"


# ========================================================================
# reply_to_comment
# ========================================================================


def test_reply_to_comment_posts_message(monkeypatch):
    """reply_to_comment should POST /{comment-id}/replies with message."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"id": "reply1"})], calls),
    )
    result = ig_common.reply_to_comment(FAKE_COMMENT_ID, "Thanks for the feedback!", FAKE_TOKEN)
    assert result["id"] == "reply1"
    call = calls[0]
    assert call["method"] == "POST"
    assert f"/{FAKE_COMMENT_ID}/replies" in call["url"]
    assert call["data"]["message"] == "Thanks for the feedback!"
    assert call["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"


# ========================================================================
# hide_comment
# ========================================================================


def test_hide_comment_posts_hide_true(monkeypatch):
    """hide_comment should POST /{comment-id} with hide=True."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"success": True})], calls),
    )
    result = ig_common.hide_comment(FAKE_COMMENT_ID, FAKE_TOKEN, hide=True)
    assert result["success"] is True
    call = calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith(f"/{FAKE_COMMENT_ID}")
    assert call["data"]["hide"] == "true"


def test_hide_comment_with_hide_false(monkeypatch):
    """hide_comment should support unhiding with hide=False."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"success": True})], calls),
    )
    ig_common.hide_comment(FAKE_COMMENT_ID, FAKE_TOKEN, hide=False)
    call = calls[0]
    assert call["data"]["hide"] == "false"


# ========================================================================
# delete_comment
# ========================================================================


def test_delete_comment_sends_delete_request(monkeypatch):
    """delete_comment should DELETE /{comment-id}."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"success": True})], calls),
    )
    result = ig_common.delete_comment(FAKE_COMMENT_ID, FAKE_TOKEN)
    assert result["success"] is True
    call = calls[0]
    assert call["method"] == "DELETE"
    assert call["url"].endswith(f"/{FAKE_COMMENT_ID}")
    assert call["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"


def test_delete_comment_error_is_redacted(monkeypatch):
    """delete_comment errors should not contain the token."""
    calls = []
    leaky = requests.HTTPError(
        f"403 Forbidden for url: https://graph.instagram.com/v21.0/{FAKE_COMMENT_ID}?access_token={FAKE_TOKEN}"
    )
    monkeypatch.setattr(ig_common, "requests", fake_requests([leaky], calls))
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.delete_comment(FAKE_COMMENT_ID, FAKE_TOKEN)
    assert FAKE_TOKEN not in str(exc.value)


# ========================================================================
# account_insights
# ========================================================================


def test_account_insights_gets_correct_endpoint(monkeypatch):
    """account_insights should GET /me/insights with metrics, period, metric_type."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests(
            [FakeResponse({"data": [{"name": "reach", "period": "day", "values": [{"value": 1000}]}]})],
            calls,
        ),
    )
    result = ig_common.account_insights(FAKE_TOKEN)
    assert len(result) == 1
    assert result[0]["name"] == "reach"
    call = calls[0]
    assert call["method"] == "GET"
    assert "/me/insights" in call["url"]
    assert call["params"]["metric"] == "reach,accounts_engaged"
    assert call["params"]["period"] == "day"
    assert call["params"]["metric_type"] == "total_value"


def test_account_insights_with_custom_metrics(monkeypatch):
    """account_insights should accept custom metrics tuple."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"data": []})], calls),
    )
    ig_common.account_insights(
        FAKE_TOKEN, metrics=("profile_views", "website_clicks"), period="week"
    )
    call = calls[0]
    assert call["params"]["metric"] == "profile_views,website_clicks"
    assert call["params"]["period"] == "week"


# ========================================================================
# media_insights
# ========================================================================


def test_media_insights_gets_correct_endpoint(monkeypatch):
    """media_insights should GET /{media-id}/insights with metrics."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"data": [{"name": "reach", "values": [{"value": 500}]}]})], calls),
    )
    result = ig_common.media_insights(FAKE_MEDIA_ID, FAKE_TOKEN)
    assert len(result) == 1
    call = calls[0]
    assert call["method"] == "GET"
    assert f"/{FAKE_MEDIA_ID}/insights" in call["url"]
    assert call["params"]["metric"] == "reach,likes,comments,saved,shares"


def test_media_insights_with_custom_metrics(monkeypatch):
    """media_insights should accept custom metrics."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"data": []})], calls),
    )
    ig_common.media_insights(FAKE_MEDIA_ID, FAKE_TOKEN, metrics=("reach", "likes"))
    call = calls[0]
    assert call["params"]["metric"] == "reach,likes"


# ========================================================================
# list_conversations
# ========================================================================


def test_list_conversations_gets_correct_endpoint(monkeypatch):
    """list_conversations should GET /me/conversations with platform param."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests(
            [FakeResponse({"data": [{"id": "conv1", "senders": [{"name": "User"}]}]})],
            calls,
        ),
    )
    result = ig_common.list_conversations(FAKE_TOKEN)
    assert len(result) == 1
    call = calls[0]
    assert call["method"] == "GET"
    assert "/me/conversations" in call["url"]
    assert call["params"]["platform"] == "instagram"


# ========================================================================
# list_messages
# ========================================================================


def test_list_messages_gets_correct_endpoint(monkeypatch):
    """list_messages should GET /{conversation-id}/messages with fields."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"data": [{"id": "msg1", "message": "hello"}]})], calls),
    )
    result = ig_common.list_messages(FAKE_CONVERSATION_ID, FAKE_TOKEN)
    assert len(result) == 1
    call = calls[0]
    assert call["method"] == "GET"
    assert f"/{FAKE_CONVERSATION_ID}/messages" in call["url"]
    assert call["params"]["fields"] == "id,message,from,created_time"


# ========================================================================
# send_message
# ========================================================================


def test_send_message_posts_with_correct_body(monkeypatch):
    """send_message should POST /me/messages with nested recipient/message structure."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"message_id": "msg123"})], calls),
    )
    result = ig_common.send_message(FAKE_RECIPIENT_ID, "Hi there!", FAKE_TOKEN)
    assert result["message_id"] == "msg123"
    call = calls[0]
    assert call["method"] == "POST"
    assert "/me/messages" in call["url"]
    assert call["data"]["recipient"]["id"] == FAKE_RECIPIENT_ID
    assert call["data"]["message"]["text"] == "Hi there!"
    assert call["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"


def test_send_message_error_is_redacted(monkeypatch):
    """send_message errors should not contain the token."""
    calls = []
    leaky = requests.HTTPError(
        f"429 Too Many Requests for url: https://graph.instagram.com/v21.0/me/messages?access_token={FAKE_TOKEN}"
    )
    monkeypatch.setattr(ig_common, "requests", fake_requests([leaky], calls))
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.send_message(FAKE_RECIPIENT_ID, "Hi", FAKE_TOKEN)
    assert FAKE_TOKEN not in str(exc.value)


# ========================================================================
# publish_image
# ========================================================================


def test_publish_image_creates_container_polls_and_publishes(monkeypatch):
    """publish_image should create container, poll, then publish."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests(
            [
                FakeResponse({"id": "container1"}),  # create container
                FakeResponse({"status_code": "FINISHED"}),  # poll
                FakeResponse({"id": "media123"}),  # publish
            ],
            calls,
        ),
    )
    result = ig_common.publish_image(
        "https://example.test/img.jpg", "Check this out!", FAKE_TOKEN
    )
    assert result == "media123"
    assert len(calls) == 3
    # First call: create container
    assert calls[0]["method"] == "POST"
    assert f"/{FAKE_USER_ID}/media" in calls[0]["url"]
    assert calls[0]["data"]["image_url"] == "https://example.test/img.jpg"
    assert calls[0]["data"]["caption"] == "Check this out!"
    # Second call: poll
    assert calls[1]["method"] == "GET"
    assert "/container1" in calls[1]["url"]
    assert "status_code" in calls[1]["params"]["fields"]
    # Third call: publish
    assert calls[2]["method"] == "POST"
    assert f"/{FAKE_USER_ID}/media_publish" in calls[2]["url"]
    assert calls[2]["data"]["creation_id"] == "container1"


def test_publish_image_with_custom_user_id(monkeypatch):
    """publish_image should accept custom user_id."""
    calls = []
    custom_user_id = "99999999999999999"
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests(
            [
                FakeResponse({"id": "container1"}),
                FakeResponse({"status_code": "FINISHED"}),
                FakeResponse({"id": "media123"}),
            ],
            calls,
        ),
    )
    ig_common.publish_image(
        "https://example.test/img.jpg",
        "Test",
        FAKE_TOKEN,
        user_id=custom_user_id,
    )
    assert f"/{custom_user_id}/media" in calls[0]["url"]


def test_publish_image_fails_if_container_status_error(monkeypatch):
    """publish_image should raise if container status is ERROR."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests(
            [
                FakeResponse({"id": "container1"}),
                FakeResponse({"status_code": "ERROR"}),
            ],
            calls,
        ),
    )
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.publish_image("https://example.test/img.jpg", "Test", FAKE_TOKEN)
    assert "failed processing" in str(exc.value)


def test_publish_image_polls_until_timeout(monkeypatch):
    """publish_image should timeout if container takes too long."""
    calls = []
    # Return "IN_PROGRESS" many times to simulate a slow container and trigger timeout
    responses = [FakeResponse({"id": "container1"})]  # create container
    # Add many "IN_PROGRESS" responses to trigger timeout (60 / 3 = 20 polling attempts)
    for _ in range(25):
        responses.append(FakeResponse({"status_code": "IN_PROGRESS"}))

    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests(responses, calls),
    )
    # Mock time so the poll loop doesn't actually sleep through the full timeout.
    import time as _t
    clock = {"t": 0.0}
    monkeypatch.setattr(_t, "sleep", lambda s: clock.__setitem__("t", clock["t"] + s))
    monkeypatch.setattr(_t, "time", lambda: clock["t"])
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.publish_image("https://example.test/img.jpg", "Test", FAKE_TOKEN)
    assert "timed out" in str(exc.value)


def test_publish_image_no_container_id_raises_error(monkeypatch):
    """publish_image should raise if create container returns no id."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({})], calls),  # No id field
    )
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.publish_image("https://example.test/img.jpg", "Test", FAKE_TOKEN)
    assert "no container id" in str(exc.value)


# ========================================================================
# publish_carousel
# ========================================================================


def test_publish_carousel_creates_items_polls_carousel_and_publishes(monkeypatch):
    """publish_carousel should create items, poll them, create carousel, poll carousel, publish."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests(
            [
                FakeResponse({"id": "item1"}),  # create item 1
                FakeResponse({"id": "item2"}),  # create item 2
                FakeResponse({"status_code": "FINISHED"}),  # poll item 1
                FakeResponse({"status_code": "FINISHED"}),  # poll item 2
                FakeResponse({"id": "carousel1"}),  # create carousel
                FakeResponse({"status_code": "FINISHED"}),  # poll carousel
                FakeResponse({"id": "media456"}),  # publish
            ],
            calls,
        ),
    )
    result = ig_common.publish_carousel(
        ["https://example.test/img1.jpg", "https://example.test/img2.jpg"],
        "Carousel caption",
        FAKE_TOKEN,
    )
    assert result == "media456"
    assert len(calls) == 7
    # Create items
    assert calls[0]["method"] == "POST"
    assert calls[0]["data"]["is_carousel_item"] == "true"
    assert calls[1]["method"] == "POST"
    # Poll items
    assert calls[2]["method"] == "GET"
    assert calls[3]["method"] == "GET"
    # Create carousel
    assert calls[4]["method"] == "POST"
    assert calls[4]["data"]["media_type"] == "CAROUSEL"
    assert calls[4]["data"]["children"] == "item1,item2"
    assert calls[4]["data"]["caption"] == "Carousel caption"
    # Poll carousel
    assert calls[5]["method"] == "GET"
    # Publish
    assert calls[6]["method"] == "POST"
    assert calls[6]["data"]["creation_id"] == "carousel1"


def test_publish_carousel_requires_at_least_two_images(monkeypatch):
    """publish_carousel should reject if fewer than 2 images."""
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.publish_carousel(["https://example.test/img.jpg"], "Caption", FAKE_TOKEN)
    assert "at least 2 images" in str(exc.value)


def test_publish_carousel_with_empty_list(monkeypatch):
    """publish_carousel should reject empty image list."""
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.publish_carousel([], "Caption", FAKE_TOKEN)
    assert "at least 2 images" in str(exc.value)


def test_publish_carousel_fails_if_item_status_error(monkeypatch):
    """publish_carousel should raise if item status is ERROR."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests(
            [
                FakeResponse({"id": "item1"}),
                FakeResponse({"id": "item2"}),
                FakeResponse({"status_code": "ERROR"}),
            ],
            calls,
        ),
    )
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.publish_carousel(
            ["https://example.test/img1.jpg", "https://example.test/img2.jpg"],
            "Caption",
            FAKE_TOKEN,
        )
    assert "failed processing" in str(exc.value)


def test_publish_carousel_fails_if_carousel_status_error(monkeypatch):
    """publish_carousel should raise if carousel status is ERROR."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests(
            [
                FakeResponse({"id": "item1"}),
                FakeResponse({"id": "item2"}),
                FakeResponse({"status_code": "FINISHED"}),
                FakeResponse({"status_code": "FINISHED"}),
                FakeResponse({"id": "carousel1"}),
                FakeResponse({"status_code": "ERROR"}),
            ],
            calls,
        ),
    )
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.publish_carousel(
            ["https://example.test/img1.jpg", "https://example.test/img2.jpg"],
            "Caption",
            FAKE_TOKEN,
        )
    assert "carousel" in str(exc.value) and "failed processing" in str(exc.value)


def test_publish_carousel_with_custom_user_id(monkeypatch):
    """publish_carousel should accept custom user_id."""
    calls = []
    custom_user_id = "88888888888888888"
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests(
            [
                FakeResponse({"id": "item1"}),
                FakeResponse({"id": "item2"}),
                FakeResponse({"status_code": "FINISHED"}),
                FakeResponse({"status_code": "FINISHED"}),
                FakeResponse({"id": "carousel1"}),
                FakeResponse({"status_code": "FINISHED"}),
                FakeResponse({"id": "media456"}),
            ],
            calls,
        ),
    )
    ig_common.publish_carousel(
        ["https://example.test/img1.jpg", "https://example.test/img2.jpg"],
        "Caption",
        FAKE_TOKEN,
        user_id=custom_user_id,
    )
    assert f"/{custom_user_id}/media" in calls[0]["url"]


# ========================================================================
# api_delete
# ========================================================================


def test_api_delete_sends_bearer_header(monkeypatch):
    """api_delete should send DELETE request with Bearer header."""
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"success": True})], calls),
    )
    result = ig_common.api_delete("123/something", FAKE_TOKEN)
    assert result["success"] is True
    call = calls[0]
    assert call["method"] == "DELETE"
    assert "/123/something" in call["url"]
    assert call["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"


def test_api_delete_error_is_redacted(monkeypatch):
    """api_delete errors should not contain the token."""
    calls = []
    leaky = requests.HTTPError(
        f"403 Forbidden for url: https://graph.instagram.com/v21.0/123?access_token={FAKE_TOKEN}"
    )
    monkeypatch.setattr(ig_common, "requests", fake_requests([leaky], calls))
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.api_delete("123", FAKE_TOKEN)
    assert FAKE_TOKEN not in str(exc.value)


# ========================================================================
# IG_USER_ID_GRAPH constant
# ========================================================================


def test_ig_user_id_graph_has_default_value():
    """IG_USER_ID_GRAPH should have the correct default value."""
    assert ig_common.IG_USER_ID_GRAPH == "17841440746293693"


def test_ig_user_id_graph_overridable_via_env(monkeypatch):
    """IG_USER_ID_GRAPH should be overridable via env var."""
    custom_id = "99999999999999999"
    # Re-import to pick up the new env var
    monkeypatch.setenv("IG_USER_ID_GRAPH", custom_id)
    # Need to reload the module to pick up the env var at import time
    import importlib

    importlib.reload(ig_common)
    assert ig_common.IG_USER_ID_GRAPH == custom_id
