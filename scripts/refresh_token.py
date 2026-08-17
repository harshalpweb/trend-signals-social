"""Refresh the long-lived Instagram access token before it expires (~60 days),
and write the new token back into this repo's GitHub Secret.

Run monthly by .github/workflows/refresh_token.yml. Requires:
- IG_ACCESS_TOKEN: current long-lived token (secret)
- REPO_ADMIN_TOKEN: a fine-grained GitHub PAT scoped to THIS repo only, with
  "Secrets: Read and write" permission — needed because the default
  GITHUB_TOKEN Actions provides cannot manage repo secrets (by design).
- GITHUB_REPOSITORY: auto-provided by Actions as "owner/repo"
"""
import base64
import os
import sys

import requests
from nacl import encoding, public

REFRESH_URL = "https://graph.instagram.com/refresh_access_token"


def refresh_ig_token(current_token: str) -> str:
    resp = requests.get(
        REFRESH_URL,
        params={"grant_type": "ig_refresh_token", "access_token": current_token},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        raise RuntimeError(f"unexpected refresh response: {data}")
    return data["access_token"]


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

    new_token = refresh_ig_token(current_token)
    update_github_secret(repo, admin_token, "IG_ACCESS_TOKEN", new_token)
    print("IG_ACCESS_TOKEN refreshed and updated successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 - any failure here must fail the workflow loudly
        print(f"Token refresh FAILED: {e}", file=sys.stderr)
        sys.exit(1)
