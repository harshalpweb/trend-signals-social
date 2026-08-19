"""Shared Meta Graph client for every rail in this repo.

Two jobs:

1. **No token ever leaks.** `requests` puts the full request URL — query string
   included — into `HTTPError`/`RequestException` messages. Any call that passes
   `access_token=` as a query param therefore turns an ordinary 400 into a secret
   printed to stdout, written into `post["last_error"]`, and committed to git by
   publish.yml's `if: always()` step. So: the token travels in an
   `Authorization: Bearer` header, and *every* string that leaves this module is
   put through `redact()` as a second line of defence.

2. **Host-switchable auth model.** Meta has two incompatible Instagram auth
   models and we are mid-migration between them:

   | `IG_AUTH_MODE`     | host                       | token   | refresh |
   |--------------------|----------------------------|---------|---------|
   | `instagram_login`  | `graph.instagram.com`      | `IGAA…` | `/refresh_access_token?grant_type=ig_refresh_token` |
   | `facebook_login`   | `graph.facebook.com`       | `EAA…`  | `/{v}/oauth/access_token?grant_type=fb_exchange_token` |

   Default is `instagram_login` — today's live model. When the founder finishes
   Path 1 (Facebook Page linked to @trendradar.in, app moved to Facebook Login
   for Business), flipping `IG_AUTH_MODE=facebook_login` plus setting
   `META_APP_ID`/`META_APP_SECRET` switches every script at once. See the
   "Path 1 switch-over runbook" in `docs/platforms.md`.

Env vars read here (all optional except the token the caller passes in):
  IG_AUTH_MODE     instagram_login (default) | facebook_login
  GRAPH_API_VERSION  override the pinned version (default below)
  META_APP_ID / META_APP_SECRET  required only for facebook_login refresh
"""
from __future__ import annotations

import os
from typing import Any

import requests

# Single source of truth for the pinned version. v21.0 is what the live rails
# have always used; it sunsets around Oct 2026, and bumping it is this one line.
GRAPH_API_VERSION = os.environ.get("GRAPH_API_VERSION") or "v21.0"

AUTH_MODE_INSTAGRAM = "instagram_login"
AUTH_MODE_FACEBOOK = "facebook_login"
DEFAULT_AUTH_MODE = AUTH_MODE_INSTAGRAM

HOSTS = {
    AUTH_MODE_INSTAGRAM: "https://graph.instagram.com",
    AUTH_MODE_FACEBOOK: "https://graph.facebook.com",
}

DEFAULT_TIMEOUT_S = 30

# IG business-account ID for insights and publishing (the `/me` user_id from Graph API).
# Separate from the app-scoped id (which is in `/me` as id field). Overridable via env.
IG_USER_ID_GRAPH = os.environ.get("IG_USER_ID_GRAPH") or "17841440746293693"

# Values that must never appear in any string this process emits.
_SECRETS: list[str] = []


class ConfigError(Exception):
    """Missing or invalid configuration (env vars). Never carries a secret."""


class GraphAPIError(Exception):
    """A Graph call failed. `str()` of this is always redacted.

    kind: "api" (Graph returned an error payload) | "http" | "network" | "parse"
    """

    def __init__(
        self,
        message: str,
        *,
        kind: str = "api",
        code: Any = None,
        subcode: Any = None,
        err_type: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(redact(message))
        self.kind = kind
        self.code = code
        self.subcode = subcode
        self.err_type = err_type
        self.status_code = status_code


def register_secret(*values: str | None) -> None:
    """Mark values as secret so redact() scrubs them from every message."""
    for value in values:
        if value and value not in _SECRETS:
            _SECRETS.append(value)


def redact(text: object) -> str:
    """Replace every registered secret value in `text` with a placeholder."""
    out = str(text)
    for secret in _SECRETS:
        if secret:
            out = out.replace(secret, "<REDACTED>")
    return out


def auth_mode(env: dict | None = None) -> str:
    """Resolve IG_AUTH_MODE. Empty/unset -> instagram_login (today's behaviour)."""
    source = os.environ if env is None else env
    mode = (source.get("IG_AUTH_MODE") or DEFAULT_AUTH_MODE).strip().lower()
    if mode not in HOSTS:
        raise ConfigError(
            f"IG_AUTH_MODE={mode!r} is not valid; expected one of {sorted(HOSTS)}"
        )
    return mode


def graph_host(mode: str | None = None) -> str:
    return HOSTS[mode or auth_mode()]


def graph_base(mode: str | None = None, version: str | None = None) -> str:
    """Versioned API root, e.g. https://graph.instagram.com/v21.0"""
    return f"{graph_host(mode)}/{version or GRAPH_API_VERSION}"


def _parse_error_payload(payload: Any, status_code: int) -> GraphAPIError | None:
    if isinstance(payload, dict) and payload.get("error"):
        err = payload["error"] if isinstance(payload["error"], dict) else {}
        return GraphAPIError(
            f"{err.get('type', 'Error')} code={err.get('code', '?')}: "
            f"{err.get('message', payload['error'])}",
            kind="api",
            code=err.get("code"),
            subcode=err.get("error_subcode"),
            err_type=err.get("type"),
            status_code=status_code,
        )
    return None


def _request(
    method: str,
    url: str,
    token: str,
    *,
    params: dict | None = None,
    data: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT_S,
    session: Any = None,
    _param_auth: bool = False,
) -> dict:
    """One Graph call. Returns parsed JSON; raises GraphAPIError (redacted).

    Auth goes in the Authorization header. `graph.instagram.com` historically
    only documented the `access_token` query param, so on an auth-shaped failure
    we retry once with the token as a param — an auth failure means nothing was
    performed server-side, so the retry cannot duplicate a post. Redaction still
    covers the param form.
    """
    register_secret(token)
    http = session or requests
    call_params = dict(params or {})
    call_data = dict(data or {})
    headers = {}
    if _param_auth:
        if method == "GET":
            call_params["access_token"] = token
        else:
            call_data["access_token"] = token
    else:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if method == "GET":
            resp = http.get(url, params=call_params, headers=headers, timeout=timeout)
        else:
            resp = http.post(
                url, data=call_data, params=call_params, headers=headers, timeout=timeout
            )
    except requests.RequestException as e:
        raise GraphAPIError(f"network error calling {url}: {e}", kind="network") from None

    try:
        payload = resp.json()
    except ValueError:
        raise GraphAPIError(
            f"non-JSON response (HTTP {resp.status_code}) from {url}: "
            f"{redact(resp.text)[:300]}",
            kind="parse",
            status_code=resp.status_code,
        ) from None

    api_error = _parse_error_payload(payload, resp.status_code)
    if api_error is not None:
        if not _param_auth and _is_auth_shaped(api_error):
            # Header auth rejected -> fall back once to query-param auth.
            return _request(
                method,
                url,
                token,
                params=params,
                data=data,
                timeout=timeout,
                session=session,
                _param_auth=True,
            )
        raise api_error

    if resp.status_code >= 400:
        raise GraphAPIError(
            f"HTTP {resp.status_code} from {url}: {redact(payload)}",
            kind="http",
            status_code=resp.status_code,
        )
    return payload


def _is_auth_shaped(error: GraphAPIError) -> bool:
    """True for 'no/unparseable token' errors — i.e. the header wasn't honoured.

    Deliberately narrow: code 190 only, and only the 'missing/unparseable'
    wordings. A genuinely expired token also matches, but the retry then fails
    identically, so the diagnosis is unchanged.
    """
    if error.code != 190:
        return False
    text = str(error).lower()
    return "access token" in text


def api_get(
    path: str,
    token: str,
    *,
    params: dict | None = None,
    base: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_S,
    session: Any = None,
) -> dict:
    """GET {base}/{path}. `path` is e.g. "me" or "<ig-user-id>/media"."""
    url = f"{base or graph_base()}/{path.lstrip('/')}"
    return _request("GET", url, token, params=params, timeout=timeout, session=session)


def api_post(
    path: str,
    token: str,
    *,
    data: dict | None = None,
    base: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_S,
    session: Any = None,
) -> dict:
    """POST {base}/{path} with a form body."""
    url = f"{base or graph_base()}/{path.lstrip('/')}"
    return _request("POST", url, token, data=data, timeout=timeout, session=session)


def api_delete(
    path: str,
    token: str,
    *,
    base: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_S,
    session: Any = None,
) -> dict:
    """DELETE {base}/{path}. Mirroring api_post/api_get; uses Bearer header auth."""
    register_secret(token)
    http = session or requests
    url = f"{base or graph_base()}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = http.delete(url, headers=headers, timeout=timeout)
    except requests.RequestException as e:
        raise GraphAPIError(f"network error calling {url}: {e}", kind="network") from None

    try:
        payload = resp.json()
    except ValueError:
        raise GraphAPIError(
            f"non-JSON response (HTTP {resp.status_code}) from {url}: "
            f"{redact(resp.text)[:300]}",
            kind="parse",
            status_code=resp.status_code,
        ) from None

    api_error = _parse_error_payload(payload, resp.status_code)
    if api_error is not None:
        raise api_error

    if resp.status_code >= 400:
        raise GraphAPIError(
            f"HTTP {resp.status_code} from {url}: {redact(payload)}",
            kind="http",
            status_code=resp.status_code,
        )
    return payload


# ========================================================================
# Instagram Control Functions
# ========================================================================


def list_media(
    token: str,
    *,
    limit: int = 25,
    fields: str = "id,caption,media_type,permalink,timestamp,comments_count,like_count",
) -> list:
    """GET /me/media — list media (photos/videos) on the business account.

    Args:
        token: Access token
        limit: Max number of media to return (default 25)
        fields: Comma-separated fields to include in response

    Returns:
        List of media objects (dicts)

    Raises:
        GraphAPIError on API/network failure
    """
    payload = api_get(
        "me/media",
        token,
        params={"fields": fields, "limit": limit},
    )
    return payload.get("data", [])


def list_comments(
    media_id: str,
    token: str,
    *,
    fields: str = "id,text,username,timestamp,like_count",
) -> list:
    """GET /{media-id}/comments — list comments on a piece of media.

    Args:
        media_id: The media ID
        token: Access token
        fields: Comma-separated fields to include in response

    Returns:
        List of comment objects (dicts)

    Raises:
        GraphAPIError on API/network failure
    """
    payload = api_get(
        f"{media_id}/comments",
        token,
        params={"fields": fields},
    )
    return payload.get("data", [])


def reply_to_comment(
    comment_id: str,
    message: str,
    token: str,
) -> dict:
    """POST /{comment-id}/replies — reply to a comment.

    Args:
        comment_id: The comment ID
        message: The reply text
        token: Access token

    Returns:
        Comment object (dict) with id field

    Raises:
        GraphAPIError on API/network failure
    """
    return api_post(
        f"{comment_id}/replies",
        token,
        data={"message": message},
    )


def hide_comment(
    comment_id: str,
    token: str,
    hide: bool = True,
) -> dict:
    """POST /{comment-id} — hide or unhide a comment.

    Args:
        comment_id: The comment ID
        token: Access token
        hide: True to hide, False to unhide

    Returns:
        API response (dict) with success status

    Raises:
        GraphAPIError on API/network failure
    """
    # Graph API expects lowercase string booleans; a raw Python bool form-encodes
    # as "True"/"False" (capitalized), which the API may reject.
    return api_post(
        comment_id,
        token,
        data={"hide": "true" if hide else "false"},
    )


def delete_comment(
    comment_id: str,
    token: str,
) -> dict:
    """DELETE /{comment-id} — delete a comment.

    Args:
        comment_id: The comment ID
        token: Access token

    Returns:
        API response (dict) with success status

    Raises:
        GraphAPIError on API/network failure
    """
    return api_delete(comment_id, token)


def account_insights(
    token: str,
    *,
    metrics: tuple[str, ...] = ("reach", "accounts_engaged"),
    period: str = "day",
    metric_type: str = "total_value",
) -> list:
    """GET /me/insights — fetch insights for the business account.

    Args:
        token: Access token
        metrics: Tuple of metric names (e.g. reach, accounts_engaged, profile_views)
        period: Period for insights (day, week, month, lifetime)
        metric_type: Type of metric (total_value, lifetime_value, etc)

    Returns:
        List of insight objects (dicts)

    Raises:
        GraphAPIError on API/network failure
    """
    payload = api_get(
        "me/insights",
        token,
        params={
            "metric": ",".join(metrics),
            "period": period,
            "metric_type": metric_type,
        },
    )
    return payload.get("data", [])


def media_insights(
    media_id: str,
    token: str,
    *,
    metrics: tuple[str, ...] = ("reach", "likes", "comments", "saved", "shares"),
) -> list:
    """GET /{media-id}/insights — fetch insights for a specific piece of media.

    Args:
        media_id: The media ID
        token: Access token
        metrics: Tuple of metric names

    Returns:
        List of insight objects (dicts)

    Raises:
        GraphAPIError on API/network failure
    """
    payload = api_get(
        f"{media_id}/insights",
        token,
        params={"metric": ",".join(metrics)},
    )
    return payload.get("data", [])


def list_conversations(
    token: str,
    *,
    platform: str = "instagram",
) -> list:
    """GET /me/conversations — list conversations (DMs).

    Args:
        token: Access token
        platform: Platform filter (instagram, messenger, etc)

    Returns:
        List of conversation objects (dicts)

    Raises:
        GraphAPIError on API/network failure
    """
    payload = api_get(
        "me/conversations",
        token,
        params={"platform": platform},
    )
    return payload.get("data", [])


def list_messages(
    conversation_id: str,
    token: str,
    *,
    fields: str = "id,message,from,created_time",
) -> list:
    """GET /{conversation-id}/messages — list messages in a conversation.

    Args:
        conversation_id: The conversation ID
        token: Access token
        fields: Comma-separated fields to include

    Returns:
        List of message objects (dicts)

    Raises:
        GraphAPIError on API/network failure
    """
    payload = api_get(
        f"{conversation_id}/messages",
        token,
        params={"fields": fields},
    )
    return payload.get("data", [])


def send_message(
    recipient_id: str,
    text: str,
    token: str,
) -> dict:
    """POST /me/messages — send a direct message.

    Note: Instagram enforces a 24-hour message window — you can only send to
    users who have recently messaged you. Attempting to send outside this
    window will result in an error. This function does not enforce the window;
    the API will reject if you violate it.

    Args:
        recipient_id: The user ID of the recipient
        text: The message text
        token: Access token

    Returns:
        API response (dict) with message ID

    Raises:
        GraphAPIError on API/network failure
    """
    return api_post(
        "me/messages",
        token,
        data={
            "recipient": {"id": recipient_id},
            "message": {"text": text},
        },
    )


def publish_image(
    image_url: str,
    caption: str,
    token: str,
    *,
    user_id: str | None = None,
) -> str:
    """Publish a single image to Instagram (two-step: create container + publish).

    Creates a media container, waits for it to finish processing, then publishes it.
    Uses the standard publish_due_posts.py polling loop.

    Args:
        image_url: Public URL of the image
        caption: Caption for the post
        token: Access token
        user_id: IG business account ID (defaults to IG_USER_ID_GRAPH)

    Returns:
        The published media ID

    Raises:
        GraphAPIError on API/network failure or container processing error
    """
    import time

    user_id = user_id or IG_USER_ID_GRAPH
    base = graph_base()

    # Step 1: Create container
    payload = api_post(
        f"{user_id}/media",
        token,
        data={
            "image_url": image_url,
            "caption": caption,
        },
        base=base,
    )
    container_id = payload.get("id")
    if not container_id:
        raise GraphAPIError(
            f"publish_image: no container id in response: {redact(payload)}",
            kind="parse",
        )

    # Step 2: Poll until finished (60s timeout, 3s interval)
    deadline = time.time() + 60
    while time.time() < deadline:
        payload = api_get(
            container_id,
            token,
            params={"fields": "status_code"},
            base=base,
        )
        status = payload.get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise GraphAPIError(
                f"publish_image: container {container_id} failed processing",
                kind="api",
            )
        time.sleep(3)
    else:
        raise GraphAPIError(
            f"publish_image: container {container_id} timed out waiting to finish",
            kind="api",
        )

    # Step 3: Publish
    payload = api_post(
        f"{user_id}/media_publish",
        token,
        data={"creation_id": container_id},
        base=base,
    )
    return payload.get("id", "")


def publish_carousel(
    image_urls: list[str],
    caption: str,
    token: str,
    *,
    user_id: str | None = None,
) -> str:
    """Publish a carousel (multi-image post) to Instagram (three-step flow).

    Creates item containers for each image, waits for them to finish, creates a
    carousel container with all items, waits for that to finish, then publishes.
    Uses the standard publish_due_posts.py polling loop.

    Args:
        image_urls: List of public image URLs (2-10 images)
        caption: Caption for the carousel
        token: Access token
        user_id: IG business account ID (defaults to IG_USER_ID_GRAPH)

    Returns:
        The published media ID

    Raises:
        GraphAPIError on API/network failure or container processing error
    """
    import time

    user_id = user_id or IG_USER_ID_GRAPH
    base = graph_base()

    if not image_urls or len(image_urls) < 2:
        raise GraphAPIError(
            "publish_carousel: at least 2 images required",
            kind="api",
        )

    # Step 1: Create item containers for each image
    item_ids = []
    for image_url in image_urls:
        payload = api_post(
            f"{user_id}/media",
            token,
            data={
                "image_url": image_url,
                "is_carousel_item": "true",
            },
            base=base,
        )
        item_id = payload.get("id")
        if not item_id:
            raise GraphAPIError(
                f"publish_carousel: no item id in response: {redact(payload)}",
                kind="parse",
            )
        item_ids.append(item_id)

    # Step 2: Poll until all items finished
    deadline = time.time() + 60
    for item_id in item_ids:
        item_deadline = deadline
        while time.time() < item_deadline:
            payload = api_get(
                item_id,
                token,
                params={"fields": "status_code"},
                base=base,
            )
            status = payload.get("status_code")
            if status == "FINISHED":
                break
            if status == "ERROR":
                raise GraphAPIError(
                    f"publish_carousel: item {item_id} failed processing",
                    kind="api",
                )
            time.sleep(3)
        else:
            raise GraphAPIError(
                f"publish_carousel: item {item_id} timed out waiting to finish",
                kind="api",
            )

    # Step 3: Create carousel container
    payload = api_post(
        f"{user_id}/media",
        token,
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(item_ids),
            "caption": caption,
        },
        base=base,
    )
    carousel_id = payload.get("id")
    if not carousel_id:
        raise GraphAPIError(
            f"publish_carousel: no carousel id in response: {redact(payload)}",
            kind="parse",
        )

    # Step 4: Poll carousel until finished
    deadline = time.time() + 60
    while time.time() < deadline:
        payload = api_get(
            carousel_id,
            token,
            params={"fields": "status_code"},
            base=base,
        )
        status = payload.get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise GraphAPIError(
                f"publish_carousel: carousel {carousel_id} failed processing",
                kind="api",
            )
        time.sleep(3)
    else:
        raise GraphAPIError(
            f"publish_carousel: carousel {carousel_id} timed out waiting to finish",
            kind="api",
        )

    # Step 5: Publish
    payload = api_post(
        f"{user_id}/media_publish",
        token,
        data={"creation_id": carousel_id},
        base=base,
    )
    return payload.get("id", "")


def build_refresh_request(
    current_token: str,
    mode: str | None = None,
    *,
    app_id: str | None = None,
    app_secret: str | None = None,
    version: str | None = None,
) -> tuple[str, dict, bool]:
    """(url, params, token_in_params) for the long-lived-token refresh call.

    Split out from refresh_token() so the URL construction is unit-testable with
    a fake token/app id and no network. `token_in_params` is True for the
    facebook_login flow, where Meta requires the token as `fb_exchange_token`
    (there is no header form) — hence redaction is mandatory around it.
    """
    mode = mode or auth_mode()
    if mode == AUTH_MODE_INSTAGRAM:
        # Unversioned, as Meta documents it and as this rail has always called it.
        return (
            f"{graph_host(mode)}/refresh_access_token",
            {"grant_type": "ig_refresh_token"},
            False,
        )

    app_id = app_id or os.environ.get("META_APP_ID")
    app_secret = app_secret or os.environ.get("META_APP_SECRET")
    missing = [
        name
        for name, value in (("META_APP_ID", app_id), ("META_APP_SECRET", app_secret))
        if not value
    ]
    if missing:
        raise ConfigError(
            f"IG_AUTH_MODE=facebook_login needs {', '.join(missing)} to refresh the token"
        )
    register_secret(app_secret)
    return (
        f"{graph_host(mode)}/{version or GRAPH_API_VERSION}/oauth/access_token",
        {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": current_token,
        },
        True,
    )


def refresh_token(
    current_token: str,
    mode: str | None = None,
    *,
    app_id: str | None = None,
    app_secret: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_S,
    session: Any = None,
) -> str:
    """Exchange the current long-lived token for a fresh one. Returns the token."""
    register_secret(current_token)
    url, params, token_in_params = build_refresh_request(
        current_token, mode, app_id=app_id, app_secret=app_secret
    )
    http = session or requests
    if token_in_params:
        try:
            resp = http.get(url, params=params, timeout=timeout)
        except requests.RequestException as e:
            raise GraphAPIError(f"network error calling {url}: {e}", kind="network") from None
        try:
            data = resp.json()
        except ValueError:
            raise GraphAPIError(
                f"non-JSON refresh response (HTTP {resp.status_code}): "
                f"{redact(resp.text)[:300]}",
                kind="parse",
                status_code=resp.status_code,
            ) from None
        api_error = _parse_error_payload(data, resp.status_code)
        if api_error is not None:
            raise api_error
        if resp.status_code >= 400:
            raise GraphAPIError(
                f"HTTP {resp.status_code} from refresh: {redact(data)}",
                kind="http",
                status_code=resp.status_code,
            )
    else:
        data = _request(
            "GET", url, current_token, params=params, timeout=timeout, session=session
        )

    new_token = data.get("access_token") if isinstance(data, dict) else None
    if not new_token:
        raise GraphAPIError(
            f"unexpected refresh response (no access_token): {redact(data)}", kind="parse"
        )
    register_secret(new_token)
    return new_token
