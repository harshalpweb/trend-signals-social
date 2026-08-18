"""Tests for the shared Graph client. No network: `requests` is always faked.

Two things are being protected here:
  1. No access token may ever reach a log line, an exception message, or
     content/queue/*.json (which publish.yml commits to the repo).
  2. IG_AUTH_MODE must switch host + refresh flow between the Instagram-Login
     model we run today and the Facebook-Login model Path 1 moves us to.
"""
import importlib
import json
import sys
from types import SimpleNamespace

import pytest
import requests

import ig_common

FAKE_TOKEN = "IGAAFAKEtoken0000000000000000000000000000000000SECRETVALUE"
FAKE_APP_SECRET = "fake-app-secret-0123456789"

_NO_JSON = object()


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in ("IG_AUTH_MODE", "META_APP_ID", "META_APP_SECRET", "GRAPH_API_VERSION"):
        monkeypatch.delenv(name, raising=False)
    # _SECRETS is module-global; keep tests independent of each other.
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
        RequestException=requests.RequestException,
    )


# --------------------------------------------------------------------------
# host / version selection
# --------------------------------------------------------------------------


def test_default_mode_is_instagram_login():
    assert ig_common.auth_mode() == "instagram_login"
    assert ig_common.graph_base() == "https://graph.instagram.com/v21.0"


def test_empty_env_falls_back_to_default(monkeypatch):
    # GitHub Actions renders an unset variable as "", which must not be an error.
    monkeypatch.setenv("IG_AUTH_MODE", "")
    assert ig_common.graph_base() == "https://graph.instagram.com/v21.0"


def test_facebook_login_selects_graph_facebook(monkeypatch):
    monkeypatch.setenv("IG_AUTH_MODE", "facebook_login")
    assert ig_common.auth_mode() == "facebook_login"
    assert ig_common.graph_base() == "https://graph.facebook.com/v21.0"


def test_mode_is_case_insensitive_and_trimmed(monkeypatch):
    monkeypatch.setenv("IG_AUTH_MODE", "  Facebook_Login ")
    assert ig_common.graph_host() == "https://graph.facebook.com"


def test_unknown_mode_raises_config_error(monkeypatch):
    monkeypatch.setenv("IG_AUTH_MODE", "carrier_pigeon")
    with pytest.raises(ig_common.ConfigError):
        ig_common.auth_mode()


def test_version_is_one_constant():
    assert ig_common.GRAPH_API_VERSION == "v21.0"
    assert ig_common.graph_base(version="v23.0").endswith("/v23.0")


# --------------------------------------------------------------------------
# refresh URL construction (no network)
# --------------------------------------------------------------------------


def test_instagram_refresh_url_keeps_token_out_of_params():
    url, params, token_in_params = ig_common.build_refresh_request(
        FAKE_TOKEN, "instagram_login"
    )
    assert url == "https://graph.instagram.com/refresh_access_token"
    assert params == {"grant_type": "ig_refresh_token"}
    assert token_in_params is False
    assert FAKE_TOKEN not in json.dumps(params)


def test_facebook_refresh_url_uses_fb_exchange_token():
    url, params, token_in_params = ig_common.build_refresh_request(
        FAKE_TOKEN, "facebook_login", app_id="123456", app_secret=FAKE_APP_SECRET
    )
    assert url == "https://graph.facebook.com/v21.0/oauth/access_token"
    assert params["grant_type"] == "fb_exchange_token"
    assert params["client_id"] == "123456"
    assert params["client_secret"] == FAKE_APP_SECRET
    assert params["fb_exchange_token"] == FAKE_TOKEN
    assert token_in_params is True


def test_facebook_refresh_requires_app_credentials(monkeypatch):
    monkeypatch.setenv("IG_AUTH_MODE", "facebook_login")
    with pytest.raises(ig_common.ConfigError) as exc:
        ig_common.build_refresh_request(FAKE_TOKEN)
    assert "META_APP_ID" in str(exc.value)
    assert FAKE_TOKEN not in str(exc.value)


def test_refresh_token_facebook_flow_returns_new_token(monkeypatch):
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"access_token": "EAAnewtoken", "expires_in": 5183944})], calls),
    )
    new = ig_common.refresh_token(
        FAKE_TOKEN, "facebook_login", app_id="123456", app_secret=FAKE_APP_SECRET
    )
    assert new == "EAAnewtoken"
    assert calls[0]["url"] == "https://graph.facebook.com/v21.0/oauth/access_token"
    assert calls[0]["timeout"] == 30


def test_refresh_token_instagram_flow_uses_header_auth(monkeypatch):
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse({"access_token": "IGAAnewtoken"})], calls),
    )
    new = ig_common.refresh_token(FAKE_TOKEN, "instagram_login")
    assert new == "IGAAnewtoken"
    assert calls[0]["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert "access_token" not in calls[0]["params"]


def test_refresh_network_error_is_redacted(monkeypatch):
    calls = []
    boom = requests.ConnectionError(
        "Max retries exceeded with url: /v21.0/oauth/access_token"
        f"?fb_exchange_token={FAKE_TOKEN}&client_secret={FAKE_APP_SECRET}"
    )
    monkeypatch.setattr(ig_common, "requests", fake_requests([boom], calls))
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.refresh_token(
            FAKE_TOKEN, "facebook_login", app_id="123456", app_secret=FAKE_APP_SECRET
        )
    assert FAKE_TOKEN not in str(exc.value)
    assert FAKE_APP_SECRET not in str(exc.value)
    assert "<REDACTED>" in str(exc.value)


# --------------------------------------------------------------------------
# api_get / api_post
# --------------------------------------------------------------------------


def test_api_get_sends_bearer_header_and_no_token_param(monkeypatch):
    calls = []
    monkeypatch.setattr(
        ig_common, "requests", fake_requests([FakeResponse({"id": "1", "username": "x"})], calls)
    )
    payload = ig_common.api_get("me", FAKE_TOKEN, params={"fields": "id,username"})
    assert payload["username"] == "x"
    call = calls[0]
    assert call["url"] == "https://graph.instagram.com/v21.0/me"
    assert call["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert "access_token" not in call["params"]
    assert FAKE_TOKEN not in call["url"]


def test_api_post_sends_bearer_header(monkeypatch):
    calls = []
    monkeypatch.setattr(ig_common, "requests", fake_requests([FakeResponse({"id": "c1"})], calls))
    payload = ig_common.api_post(
        "17841400/media", FAKE_TOKEN, data={"image_url": "https://example.test/y.png"}
    )
    assert payload["id"] == "c1"
    assert calls[0]["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert "access_token" not in calls[0]["data"]


def test_api_error_payload_becomes_graph_api_error(monkeypatch):
    calls = []
    error = {
        "error": {
            "message": "API access blocked.",
            "type": "OAuthException",
            "code": 200,
            "fbtrace_id": "abc",
        }
    }
    monkeypatch.setattr(ig_common, "requests", fake_requests([FakeResponse(error, 400)], calls))
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.api_get("me", FAKE_TOKEN)
    assert exc.value.code == 200
    assert exc.value.kind == "api"
    assert exc.value.err_type == "OAuthException"
    assert "API access blocked." in str(exc.value)


def test_http_error_message_never_contains_the_token(monkeypatch):
    """The exact job-1 leak vector: a requests error carrying the request URL."""
    calls = []
    leaky = requests.HTTPError(
        "400 Client Error for url: https://graph.instagram.com/v21.0/17841400/media"
        f"?access_token={FAKE_TOKEN}"
    )
    monkeypatch.setattr(ig_common, "requests", fake_requests([leaky], calls))
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.api_post("17841400/media", FAKE_TOKEN, data={"x": "1"})
    assert FAKE_TOKEN not in str(exc.value)
    assert "<REDACTED>" in str(exc.value)


def test_non_json_response_is_reported_without_token(monkeypatch):
    calls = []
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse(_NO_JSON, 502, text=f"gateway error {FAKE_TOKEN}")], calls),
    )
    with pytest.raises(ig_common.GraphAPIError) as exc:
        ig_common.api_get("me", FAKE_TOKEN)
    assert exc.value.kind == "parse"
    assert FAKE_TOKEN not in str(exc.value)


def test_auth_shaped_190_falls_back_to_param_auth_once(monkeypatch):
    calls = []
    err = {
        "error": {
            "message": "Cannot parse access token",
            "type": "OAuthException",
            "code": 190,
        }
    }
    monkeypatch.setattr(
        ig_common,
        "requests",
        fake_requests([FakeResponse(err, 400), FakeResponse({"id": "9"})], calls),
    )
    payload = ig_common.api_get("me", FAKE_TOKEN)
    assert payload["id"] == "9"
    assert len(calls) == 2
    assert "access_token" not in calls[0]["params"]
    assert calls[1]["params"]["access_token"] == FAKE_TOKEN  # fallback form


def test_non_auth_error_does_not_retry(monkeypatch):
    calls = []
    err = {"error": {"message": "API access blocked.", "type": "OAuthException", "code": 200}}
    monkeypatch.setattr(ig_common, "requests", fake_requests([FakeResponse(err, 400)], calls))
    with pytest.raises(ig_common.GraphAPIError):
        ig_common.api_get("me", FAKE_TOKEN)
    assert len(calls) == 1


def test_redact_handles_multiple_secrets():
    ig_common.register_secret(FAKE_TOKEN, FAKE_APP_SECRET)
    out = ig_common.redact(f"a={FAKE_TOKEN} b={FAKE_APP_SECRET}")
    assert out == "a=<REDACTED> b=<REDACTED>"


# --------------------------------------------------------------------------
# publish_due_posts: last_error must never carry a token
# --------------------------------------------------------------------------


def _load_publish_module(monkeypatch, tmp_path):
    monkeypatch.setenv("IG_ACCESS_TOKEN", FAKE_TOKEN)
    monkeypatch.setenv("IG_USER_ID", "17841400")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    sys.modules.pop("publish_due_posts", None)
    mod = importlib.import_module("publish_due_posts")
    monkeypatch.setattr(mod, "QUEUE_DIR", tmp_path / "queue")
    monkeypatch.setattr(mod, "POSTED_DIR", tmp_path / "posted")
    monkeypatch.setattr(mod, "FAILED_DIR", tmp_path / "failed")
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    (tmp_path / "queue").mkdir()
    return mod


def _write_due_post(queue_dir, post_id="p1"):
    (queue_dir / f"{post_id}.json").write_text(
        json.dumps(
            {
                "id": post_id,
                "type": "carousel",
                "caption": "hello",
                "slides": ["content/slides/a.png"],
                "scheduled_time_ist": "2020-01-01T00:00:00+00:00",
                "status": "pending",
            }
        ),
        encoding="utf-8",
    )


def test_no_due_posts_exits_zero(monkeypatch, tmp_path):
    mod = _load_publish_module(monkeypatch, tmp_path)
    assert mod.main() == 0


def test_forced_failure_exits_one_and_last_error_has_no_token(monkeypatch, tmp_path, capsys):
    mod = _load_publish_module(monkeypatch, tmp_path)
    _write_due_post(mod.QUEUE_DIR)
    leaky = requests.HTTPError(
        "400 Client Error: Bad Request for url: "
        f"https://graph.instagram.com/v21.0/17841400/media?access_token={FAKE_TOKEN}"
    )
    monkeypatch.setattr(ig_common, "requests", fake_requests([leaky], []))
    ig_common.register_secret(FAKE_TOKEN)

    assert mod.main() == 1

    state = json.loads((mod.QUEUE_DIR / "p1.json").read_text(encoding="utf-8"))
    assert state["attempts"] == 1
    assert state["status"] == "pending"
    assert FAKE_TOKEN not in state["last_error"]
    assert "<REDACTED>" in state["last_error"]
    # ...and nothing printed to stdout/stderr carries it either.
    captured = capsys.readouterr()
    assert FAKE_TOKEN not in captured.out
    assert FAKE_TOKEN not in captured.err
