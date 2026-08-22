# -*- coding: utf-8 -*-
"""Pulihkan env Pages: PATCH dengan NILAI LENGKAP semua kunci (pola set_pages_env.py).

Pelajaran insiden 22 Agu 2026: PATCH deployment_configs yang mengirim entri
secret_text TANPA value menghapus nilainya. Karena itu skrip ini SELALU mengirim
nilai eksplisit untuk SEMUA kunci dalam satu PATCH.
"""
import os
import time

import requests

ACCT = "0423daf5e50d8a7d1d1d4a63fd4e69bd"
PROJ = "mtms-aqua-haier-kb"

cred_dir = os.path.join("D:", os.sep, "Secret")
pages_tok = open(os.path.join(cred_dir, "cloudflare-pages-token.txt"), encoding="utf-8").read().strip()
gh_file = open(os.path.join(cred_dir, "github api key.txt"), encoding="utf-8").read().strip()
BASE = f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/pages/projects/{PROJ}"
HDR = {"Authorization": "Bearer " + pages_tok, "Content-Type": "application/json"}

import subprocess
gh_keyring = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()

ENV_LENGKAP = {
    "GITHUB_TOKEN": {"value": gh_file, "type": "secret_text"},
    "EDIT_PASSWORD": {"value": "MTMS-KB-Edit#2026", "type": "secret_text"},
    "LOGIN_PASSWORD": {"value": "aquaisthebest", "type": "secret_text"},
    "RESEARCH_WORKFLOW_TOKEN": {"value": gh_keyring or gh_file, "type": "secret_text"},
    "RESEARCH_WORKFLOW_REF": {"value": "master", "type": "secret_text"},
}


def api(method, url, body=None, tries=5):
    last = None
    for i in range(tries):
        try:
            return requests.request(method, url, headers=HDR, json=body, timeout=45)
        except Exception as exc:
            last = exc
            print("retry", i + 1, repr(exc)[:80])
            time.sleep(4)
    raise last


r = api("GET", BASE)
config = r.json()["result"]["deployment_configs"]
for env_name in ("production", "preview"):
    cfg = config.setdefault(env_name, {})
    if cfg.get("env_vars") is None:
        cfg["env_vars"] = {}
    cfg["env_vars"].update(ENV_LENGKAP)

r2 = api("PATCH", BASE, {"deployment_configs": config})
print("PATCH", r2.status_code)
