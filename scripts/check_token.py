"""Health probe for the Instagram access token.

Runs as a pre-step of .github/workflows/publish.yml so that an app/token problem
fails the run *before* we try to publish, and shows up as an explicit one-line
diagnosis instead of a confusing publish traceback.

Reads:
- IG_ACCESS_TOKEN: long-lived Instagram token (secret)
- IG_USER_ID:      Instagram user id (secret) - reported for confirmation only
- IG_AUTH_MODE:    instagram_login (default) | facebook_login - selects the host

Exit codes:
  0  token is live      -> "OK: token live for @<username> (id=<id>)"
  2  OAuthException     -> "FAIL: OAuthException code=<n>: <message>"
  3  missing config     -> required env var absent / bad IG_AUTH_MODE
  4  network/unexpected -> anything else

Distinguishing 2 from the rest matters operationally:
  code 190 = token invalid/expired            -> refresh_token.py / re-auth
  code 200 = "API access blocked."            -> app or account level restriction
             (Data Use Checkup overdue, business verification, dev-mode role,
             policy action) - refreshing the token will NOT fix it; check the
             Meta Developer Tools compliance findings and App Review status.

Incident throttle (opt-in, --incident-file / --due-count)
--------------------------------------------------------
An hourly cron that goes red every hour for the same known, human-blocked
incident trains the founder to ignore the alert. With --incident-file the probe
keeps a small JSON incident record and fails the run only when failing is
*informative*:

  * FIRST detection (no incident file yet) -> record it and exit 2 (run red,
    one notification).
  * Repeat detection while --due-count > 0 -> exit 2. Posts are due and cannot
    go out; that is new, actionable damage this hour.
  * Repeat detection with --due-count 0    -> print WARN, exit 0. Nothing was
    lost this hour; the incident file is the durable record and its
    checks_failed counter keeps counting, so nothing is hidden.
  * Success while an incident file exists  -> delete it, print RECOVERED, exit 0.

Deliberately NOT throttled: missing config (exit 3) and network/parse failures
(exit 4). Those are either a broken setup that must be fixed now or a transient
that clears by itself; neither is a standing incident worth suppressing.

The incident file is committed to the repo by publish.yml, so every string put
into it goes through ig_common.redact() - same rule as post["last_error"].

The token is never printed: it is sent as an Authorization header (not a query
param) and every string that leaves this script goes through ig_common.redact().
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import ig_common
from ig_common import ConfigError, GraphAPIError, api_get, graph_base, redact

EXIT_OK = 0
EXIT_OAUTH = 2
EXIT_CONFIG = 3
EXIT_OTHER = 4

HINTS = {
    200: (
        "code 200 is an app/account-level restriction, not token expiry - "
        "refreshing will not help. Check Meta Developer Tools compliance "
        "findings and App Review status."
    ),
    190: (
        "code 190 is an invalid/expired token - run refresh_token.py or "
        "re-authorise the app."
    ),
}


def _now_iso() -> str:
    """UTC timestamp, second precision, Z suffix."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_incident(path: Path) -> dict | None:
    """Parsed incident record, or None if absent / unreadable / not an object."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def record_incident(
    path: Path,
    *,
    code: object,
    message: object,
    auth_mode: str,
    hint: str,
    now: str | None = None,
) -> tuple[dict, bool]:
    """Create or update the incident record. Returns (state, is_first_detection).

    is_first_detection is True when no readable record existed - a corrupt or
    unreadable file counts as first, so a mangled file can never silence an
    alert.
    """
    stamp = now or _now_iso()
    previous = load_incident(path)
    first = previous is None
    state = {
        "first_seen_utc": stamp if first else previous.get("first_seen_utc", stamp),
        "last_seen_utc": stamp,
        "checks_failed": 1 if first else _as_int(previous.get("checks_failed")) + 1,
        "code": code,
        "message": redact(message),
        "auth_mode": auth_mode,
        "hint": redact(hint),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state, first


def clear_incident(path: Path) -> tuple[bool, dict | None]:
    """Remove the incident record. Returns (existed, last_state_or_None)."""
    existed = path.exists()
    state = load_incident(path) if existed else None
    if existed:
        path.unlink(missing_ok=True)
    return existed, state


def _due_count(value: str) -> int:
    """Parse --due-count defensively.

    An empty or unparseable value means the caller could not tell us how many
    posts are due (e.g. the counting step produced nothing). That must not be
    read as "nothing is due" - that is precisely the case where staying green
    would hide a real loss - so it degrades to 1, i.e. fail the run.
    """
    text = (value or "").strip()
    if not text:
        return 1
    try:
        return max(0, int(text))
    except ValueError:
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe the Instagram access token; optionally throttle "
        "repeat alerts for a standing incident."
    )
    parser.add_argument(
        "--incident-file",
        metavar="PATH",
        default=None,
        help="JSON incident record to create/update on OAuth failure and delete "
        "on recovery. Without it, behaviour is unchanged (always exit 2 on "
        "OAuthException).",
    )
    parser.add_argument(
        "--due-count",
        metavar="N",
        type=_due_count,
        default=0,
        help="How many posts are due right now. >0 makes a repeat incident fail "
        "the run. Empty/unparseable is treated as 1 (fail loudly).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    # argv=None means "no arguments", NOT "read sys.argv" — main() is called
    # directly from the test suite, where sys.argv holds pytest's own flags.
    # The CLI entrypoint below passes sys.argv[1:] explicitly.
    args = build_parser().parse_args([] if argv is None else argv)
    incident_path = Path(args.incident_file) if args.incident_file else None

    token = os.environ.get("IG_ACCESS_TOKEN")
    user_id = os.environ.get("IG_USER_ID")
    ig_common.register_secret(token)

    missing = [
        name
        for name, value in (("IG_ACCESS_TOKEN", token), ("IG_USER_ID", user_id))
        if not value
    ]
    if missing:
        print(f"FAIL: missing env var(s): {', '.join(missing)}", file=sys.stderr)
        return EXIT_CONFIG

    try:
        mode = ig_common.auth_mode()
        base = graph_base(mode)
    except ConfigError as e:
        print(f"FAIL: {redact(e)}", file=sys.stderr)
        return EXIT_CONFIG

    print(f"Probing {base}/me (IG_AUTH_MODE={mode})")

    try:
        payload = api_get("me", token, params={"fields": "id,username"}, base=base)
    except GraphAPIError as e:
        print(f"FAIL: {redact(e)}", file=sys.stderr)
        if e.kind != "api":
            return EXIT_OTHER
        hint = HINTS.get(e.code, "")
        if hint:
            print(f"HINT: {hint}", file=sys.stderr)
        if incident_path is None:
            return EXIT_OAUTH
        state, first = record_incident(
            incident_path,
            code=e.code,
            message=str(e),
            auth_mode=mode,
            hint=hint,
        )
        if first:
            print(
                f"INCIDENT OPENED: recorded in {incident_path} "
                f"(first detection) - failing the run.",
                file=sys.stderr,
            )
            return EXIT_OAUTH
        if args.due_count > 0:
            print(
                f"INCIDENT ongoing since {state['first_seen_utc']} "
                f"({state['checks_failed']} checks) and {args.due_count} "
                f"post(s) due - failing the run.",
                file=sys.stderr,
            )
            return EXIT_OAUTH
        print(
            f"WARN: incident ongoing since {state['first_seen_utc']} "
            f"({state['checks_failed']} checks), no due posts - "
            f"not failing the run"
        )
        return EXIT_OK

    username = payload.get("username", "?")
    returned_id = payload.get("id", "?")
    print(f"OK: token live for @{username} (id={returned_id})")
    if incident_path is not None:
        existed, previous = clear_incident(incident_path)
        if existed:
            prev = previous or {}
            print(
                f"RECOVERED: token live again - incident open since "
                f"{prev.get('first_seen_utc', '?')} "
                f"({prev.get('checks_failed', '?')} failed checks) cleared; "
                f"removed {incident_path}"
            )
    if returned_id != "?" and user_id and returned_id != user_id:
        # Not fatal - the token works - but the configured id is wrong, which
        # would make every publish call target the wrong account.
        print(
            f"WARN: IG_USER_ID env ({user_id}) != id returned by /me ({returned_id})",
            file=sys.stderr,
        )
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001 - never let a traceback leak a token
        print(f"FAIL: unexpected error: {redact(e)}", file=sys.stderr)
        sys.exit(EXIT_OTHER)
