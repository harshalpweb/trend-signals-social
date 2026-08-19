"""Finish the Meta Facebook-Login switch-over (run locally by the founder).

Reads .env (FB_USER_TOKEN, META_APP_ID, META_APP_SECRET), then:
  1. exchanges the short-lived user token for a long-lived (~60-day) one,
  2. resolves the linked Facebook Page + Instagram business-account id,
  3. writes FB_LONG_LIVED_TOKEN / INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_USER_ID /
     FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN back into .env,
  4. mirrors the meta-mcp vars into user-level Windows env vars (setx) so the
     OSS meta-mcp control plane activates on the next Claude session.

Secrets are never printed — only key names, lengths, and non-secret ids.
Run:  py -3.12 scripts/finish_meta_switchover.py
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com/v21.0"
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


def read_env(path):
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.rstrip("\n")
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def write_env(path, updates):
    """Merge updates into .env, preserving other lines and comments."""
    keys = set(updates)
    kept = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8").read().splitlines():
            head = line.split("=", 1)[0].strip() if "=" in line else ""
            if head in keys:
                continue
            if line.strip() == "# Meta FB-login credentials (2026-08-19, gitignored)":
                continue
            kept.append(line)
    kept.append("# Meta FB-login credentials (2026-08-19, gitignored)")
    for k, v in updates.items():
        kept.append(f"{k}={v}")
    open(path, "w", encoding="utf-8").write("\n".join(kept) + "\n")


def api_get(path, params, bearer=None):
    url = f"{GRAPH}{path}"
    headers = {}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    else:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code, "_body": e.read().decode(errors="ignore")[:300]}


def main():
    env = read_env(ENV_PATH)
    app_id = env.get("META_APP_ID", "")
    app_secret = env.get("META_APP_SECRET", "")
    short = env.get("FB_USER_TOKEN", "")
    if not (app_id and app_secret and short.startswith("EAA")):
        print("FATAL: .env is missing META_APP_ID / META_APP_SECRET / FB_USER_TOKEN")
        return 2

    # 1) long-lived exchange
    ll = api_get("/oauth/access_token", {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short,
    })
    long_tok = ll.get("access_token", "") if isinstance(ll, dict) else ""
    if long_tok:
        print(f"[1/4] long-lived token: OK (len {len(long_tok)}, ~60 days)")
    else:
        print(f"[1/4] long-lived exchange FAILED: {ll}")
        print("      (the short-lived token may have expired — regenerate it in Graph API Explorer)")
        return 3
    use = long_tok

    # 2) resolve Page + IG business account (header auth, no token in URL)
    acc = api_get("/me/accounts",
                  {"fields": "id,name,access_token,instagram_business_account"},
                  bearer=use)
    ig_id = page_id = page_tok = page_name = ""
    pages = acc.get("data", []) if isinstance(acc, dict) else []
    for p in pages:
        if p.get("instagram_business_account"):
            ig_id = p["instagram_business_account"]["id"]
            page_id = p.get("id", "")
            page_tok = p.get("access_token", "")
            page_name = p.get("name", "")
            break
    print(f"[2/4] pages visible via /me/accounts: {len(pages)} | IG business account: {ig_id or '(none)'}"
          + (f" via Page '{page_name}'" if page_name else ""))

    # Fallback: query the known TrendRadar Page node directly for its linked IG account.
    # (/me/accounts is empty without pages_show_list, but the Page node is still readable.)
    if not ig_id:
        known_page_id = env.get("FB_PAGE_ID", "") or "61593158354383"
        pg = api_get(f"/{known_page_id}",
                     {"fields": "name,access_token,instagram_business_account{id,username}"},
                     bearer=use)
        if isinstance(pg, dict) and pg.get("instagram_business_account"):
            iba = pg["instagram_business_account"]
            ig_id = iba.get("id", "")
            page_id = pg.get("id", known_page_id)
            page_tok = pg.get("access_token", "")
            page_name = pg.get("name", "")
            print(f"      fallback via Page node {known_page_id}: IG business account {ig_id}"
                  f" (@{iba.get('username','?')})")
        else:
            print(f"      fallback via Page node also failed: {pg}")
            print("      -> regenerate the token WITH the 'pages_show_list' permission and re-run.")

    # 3) write everything back to .env
    updates = {
        "META_APP_ID": app_id,
        "META_APP_SECRET": app_secret,
        "FB_LONG_LIVED_TOKEN": long_tok,
        "FB_USER_TOKEN": use,
    }
    if ig_id:
        updates["INSTAGRAM_ACCESS_TOKEN"] = use
        updates["INSTAGRAM_USER_ID"] = ig_id
    if page_id and page_tok:
        updates["FB_PAGE_ID"] = page_id
        updates["FB_PAGE_ACCESS_TOKEN"] = page_tok
    write_env(ENV_PATH, updates)
    print(f"[3/4] wrote to .env: {', '.join(updates)}")

    # 4) mirror meta-mcp vars into user-level Windows env vars (so the inline
    #    meta-mcp config resolves ${VAR} on the next Claude session)
    mirror = {"META_APP_ID": app_id, "META_APP_SECRET": app_secret}
    if ig_id:
        mirror["INSTAGRAM_ACCESS_TOKEN"] = use
        mirror["INSTAGRAM_USER_ID"] = ig_id
    if sys.platform == "win32":
        for k, v in mirror.items():
            subprocess.run(["setx", k, v], capture_output=True, text=True)
        print(f"[4/4] mirrored to user env vars (setx): {', '.join(mirror)}")
        print("      NOTE: restart Claude Code for the meta-mcp server to pick these up.")
    else:
        print("[4/4] (non-Windows: set these env vars yourself for meta-mcp)")

    print("\nDone. Verify with:  py -3.12 scripts/check_token.py   (IG-login pipeline unchanged)")
    print("The pipeline still runs on the existing IG-login token; the FB-login token above")
    print("activates the meta-mcp interactive control plane + Threads/Ads once you restart Claude.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
