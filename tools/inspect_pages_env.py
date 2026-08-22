# -*- coding: utf-8 -*-
"""Inspeksi env_vars Pages: kunci + ada/tidaknya field value (nilai rahasia tak dibaca/dicetak)."""
import os

import requests

ACCT = "0423daf5e50d8a7d1d1d4a63fd4e69bd"
PROJ = "mtms-aqua-haier-kb"

sec = os.path.join("D:", os.sep, "Secret")
tok = open(os.path.join(sec, "cloudflare-pages-token.txt"), encoding="utf-8").read().strip()
BASE = f"https://api.cloudflare.com/client/v4/accounts/{ACCT}/pages/projects/{PROJ}"

r = requests.get(BASE, headers={"Authorization": "Bearer " + tok}, timeout=45)
cfg = r.json()["result"]["deployment_configs"]
for env in ("production", "preview"):
    ev = cfg.get(env, {}).get("env_vars", {})
    print(env, "keys:", sorted(ev.keys()))
    for key, val in sorted(ev.items()):
        print("  ", key, "| type:", val.get("type"), "| punya field value:", "value" in val)
