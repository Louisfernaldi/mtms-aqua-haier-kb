# -*- coding: utf-8 -*-
"""Set RESEARCH_WORKFLOW_TOKEN/REF di env Pages (pola sama dengan set_pages_env.py)."""
import os
import time

import requests

ACCT = "0423daf5e50d8a7d1d1d4a63fd4e69bd"
PROJ = "mtms-aqua-haier-kb"

sec = os.path.join("D:", os.sep, "Secret")
pages_tok = open(os.path.join(sec, "cloudflare-pages-token.txt"), encoding="utf-8").read().strip()
gh_tok = open(os.path.join(sec, "github api key.txt"), encoding="utf-8").read().strip()

BASE = f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/pages/projects/{PROJ}"
HDR = {"Authorization": "Bearer " + pages_tok, "Content-Type": "application/json"}


def api(method, url, body=None, tries=5):
    last = None
    for i in range(tries):
        try:
            return requests.request(method, url, headers=HDR, json=body, timeout=45)
        except Exception as exc:  # retry jaringan
            last = exc
            print("retry", i + 1, repr(exc)[:90])
            time.sleep(4)
    raise last


r = api("GET", BASE)
config = r.json()["result"]["deployment_configs"]
env_add = {
    "RESEARCH_WORKFLOW_TOKEN": {"value": gh_tok, "type": "secret_text"},
    "RESEARCH_WORKFLOW_REF": {"value": "master", "type": "secret_text"},
}
for env_name in ("production", "preview"):
    cfg = config.setdefault(env_name, {})
    if cfg.get("env_vars") is None:
        cfg["env_vars"] = {}
    cfg["env_vars"].update(env_add)

r2 = api("PATCH", BASE, {"deployment_configs": config})
print("PATCH", r2.status_code)
res = r2.json().get("result", {}).get("deployment_configs", {})
for env_name in ("production", "preview"):
    ev = res.get(env_name, {}).get("env_vars", {})
    print(env_name, "->", {k: v.get("type") for k, v in ev.items()
                           if k.startswith("RESEARCH_")})
