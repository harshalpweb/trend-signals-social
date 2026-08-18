"""Refresh the long-lived Instagram access token before it expires (~60 days),
and write the new token back into this repo's GitHub Secret.

Run monthly by .github/workflows/refresh_token.yml. Requires:
- IG_ACCESS_TOKEN: current long-lived token (secret)
- REPO_ADMIN_TOKEN: a fine-grained GitHub PAT scoped to THIS repo only, with
  "Secrets: Read and write" permission - needed because the default
  GITHUB_TOKEN Actions provides cannot manage repo secrets (by design).
- GITHUB_REPOSITORY: auto-provided by Actions as "owner/repo"
Optional:
- IG_AUTH_MODE: instagram_login (default) | facebook_login
- META_APP_ID / META_APP_SECRET: required only when IG_AUTH_MODE=facebook_login
  (the fb_exchange_token flow needs the app credentials)

Nothing printed here can contain a secret: the Graph call goes through
ig_common (Authorization header, redacted errors) and the final catch-all
redacts too. Previously this printed the raw requests exception, whose message
embeds the request URL including access_token=.
"""
import base64
import os
import sys

import requests
from nacl import encoding, public

import ig_common
from ig_common import redact


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    public_key = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def update_github_secret(repo: str, admin_token: str, secret_name: str, secret_value: str) -> None:
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Accept": "application/vnd.github+json",
    }
    key_resp = requests.get(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers=headers,
        timeout=30,
    )
    key_resp.raise_for_status()
    key_data = key_resp.json()

    encrypted_value = encrypt_secret(key_data["key"], secret_value)

    put_resp = requests.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}",
        headers=headers,
        json={"encrypted_value": encrypted_value, "key_id": key_data["key_id"]},
        timeout=30,
    )
    put_resp.raise_for_status()


def main() -> None:
    current_token = os.environ["IG_ACCESS_TOKEN"]
    admin_token = os.environ["REPO_ADMIN_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    ig_common.register_secret(current_token, admin_token, os.environ.get("META_APP_SECRET"))

    mode = ig_common.auth_mode()
    print(f"Refreshing IG_ACCESS_TOKEN (IG_AUTH_MODE={mode})")

    new_token = ig_common.refresh_token(current_token, mode)
    ig_common.register_secret(new_token)
    update_github_secret(repo, admin_token, "IG_ACCESS_TOKEN", new_token)
    print("IG_ACCESS_TOKEN refreshed and updated successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 - any failure here must fail the workflow loudly
        # redact(): a raw requests exception embeds the request URL, which for a
        # query-param auth call would contain the token itself.
        print(f"Token refresh FAILED: {type(e).__name__}: {redact(e)}", file=sys.stderr)
        sys.exit(1)
