# -*- coding: utf-8 -*-
"""Set env vars (secret) Pages project via Cloudflare API. Pakai requests + retry.
"""
import os, json, time
import requests

ACCT = "0423daf5e50d8a7d1d1d4a63fd4e69bd"
PROJ = "mtms-aqua-haier-kb"
EDIT_PASSWORD = "MTMS-KB-Edit#2026"
LOGIN_PASSWORD = "aquaisthebest"

sec = os.path.join("D:", os.sep, "Secret")
pages_tok = open(os.path.join(sec, "cloudflare-pages-token.txt"), encoding="utf-8").read().strip()
gh_tok = open(os.path.join(sec, "github api key.txt"), encoding="utf-8").read().strip()

BASE = f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/pages/projects/{PROJ}"
HDR = {"Authorization": "Bearer " + pages_tok, "Content-Type": "application/json"}


def api(method, url, body=None, tries=5):
    last = None
    for i in range(tries):
        try:
            r = requests.request(method, url, headers=HDR, json=body, timeout=45)
            return r
        except Exception as e:
            last = e
            print("  retry", i + 1, repr(e)[:90])
            time.sleep(4)
    raise last


r = api("GET", BASE)
proj = r.json()
config = proj.get("result", {}).get("deployment_configs", {})

env_add = {
    "GITHUB_TOKEN": {"value": gh_tok, "type": "secret_text"},
    "EDIT_PASSWORD": {"value": EDIT_PASSWORD, "type": "secret_text"},
    "LOGIN_PASSWORD": {"value": LOGIN_PASSWORD, "type": "secret_text"},
}
for env in ("production", "preview"):
    cfg = config.setdefault(env, {})
    if cfg.get("env_vars") is None:
        cfg["env_vars"] = {}
    ev = cfg["env_vars"]
    for junk in ("TEST_PING",):
        ev.pop(junk, None)
    ev.update(env_add)

r2 = api("PATCH", BASE, {"deployment_configs": config})
print("PATCH", r2.status_code)
res = r2.json().get("result", {}).get("deployment_configs", {})
for env in ("production", "preview"):
    ev = res.get(env, {}).get("env_vars", {})
    print(env, "->", {k: v.get("type") for k, v in ev.items()})