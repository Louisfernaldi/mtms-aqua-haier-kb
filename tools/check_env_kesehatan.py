# -*- coding: utf-8 -*-
"""Ukur kesehatan nilai env Pages tanpa mencetak rahasia (boolean saja)."""
import os

import requests

ACCT = "0423daf5e50d8a7d1d1d4a63fd4e69bd"
PROJ = "mtms-aqua-haier-kb"
cred_dir = os.path.join("D:", os.sep, "Secret")
pages_tok = open(os.path.join(cred_dir, "cloudflare-pages-token.txt"), encoding="utf-8").read().strip()
gh_ref = open(os.path.join(cred_dir, "github api key.txt"), encoding="utf-8").read().strip()
BASE = f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/pages/projects/{PROJ}"

cfg = requests.get(BASE, headers={"Authorization": "Bearer " + pages_tok}, timeout=45
                   ).json()["result"]["deployment_configs"]

for env_name in ("production", "preview"):
    ev = cfg.get(env_name, {}).get("env_vars", {})
    login_pw = ev.get("LOGIN_PASSWORD", {}).get("value")
    gh_tok = ev.get("GITHUB_TOKEN", {}).get("value")
    ref = ev.get("RESEARCH_WORKFLOW_REF", {}).get("value")
    print(f"[{env_name}]")
    print("  LOGIN_PASSWORD == lama:", login_pw == "aquaisthebest",
          "| len:", len(login_pw or ""))
    print("  GITHUB_TOKEN == berkas referensi:", gh_tok == gh_ref,
          "| len:", len(gh_tok or ""))
    print("  RESEARCH_WORKFLOW_REF == master:", ref == "master", "| len:", len(ref or ""))

probe = requests.get("https://api.github.com/user",
                     headers={"Authorization": "Bearer " + gh_ref,
                              "User-Agent": "mtms-kb-check"}, timeout=30)
print("token referensi hidup ke GitHub:", probe.status_code == 200)
