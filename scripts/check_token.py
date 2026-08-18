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

The token is never printed: it is sent as an Authorization header (not a query
param) and every string that leaves this script goes through ig_common.redact().
"""
import os
import sys

import ig_common
from ig_common import ConfigError, GraphAPIError, api_get, graph_base, redact

EXIT_OK = 0
EXIT_OAUTH = 2
EXIT_CONFIG = 3
EXIT_OTHER = 4


def main() -> int:
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
        if e.code == 200:
            print(
                "HINT: code 200 is an app/account-level restriction, not token "
                "expiry - refreshing will not help. Check Meta Developer Tools "
                "compliance findings and App Review status.",
                file=sys.stderr,
            )
        elif e.code == 190:
            print(
                "HINT: code 190 is an invalid/expired token - run refresh_token.py "
                "or re-authorise the app.",
                file=sys.stderr,
            )
        return EXIT_OAUTH

    username = payload.get("username", "?")
    returned_id = payload.get("id", "?")
    print(f"OK: token live for @{username} (id={returned_id})")
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
        sys.exit(main())
    except Exception as e:  # noqa: BLE001 - never let a traceback leak a token
        print(f"FAIL: unexpected error: {redact(e)}", file=sys.stderr)
        sys.exit(EXIT_OTHER)
