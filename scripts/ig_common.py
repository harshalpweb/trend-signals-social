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
