# -*- coding: utf-8 -*-
"""Set ulang 5 secret Pages SATU-PER-SATU via wrangler (anti terhapus PATCH penuh).

Nilai tidak pernah dicetak. Sumber:
- LOGIN_PASSWORD / EDIT_PASSWORD: nilai baku repo (set_pages_env.py)
- GITHUB_TOKEN / RESEARCH_WORKFLOW_TOKEN: berkas kunci GitHub di folder kredensial
  dan keyring gh (untuk dispatch workflow)
- RESEARCH_WORKFLOW_REF: "master"
"""
import os
import subprocess
import sys

PROJ = "mtms-aqua-haier-kb"
cred_dir = os.path.join("D:", os.sep, "Secret")
pages_tok = open(os.path.join(cred_dir, "cloudflare-pages-token.txt"), encoding="utf-8").read().strip()
gh_file = open(os.path.join(cred_dir, "github api key.txt"), encoding="utf-8").read().strip()
gh_keyring = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()

env = dict(os.environ)
env["CLOUDFLARE_API_TOKEN"] = pages_tok

VALUES = [
    ("LOGIN_PASSWORD", "aquaisthebest"),
    ("EDIT_PASSWORD", "MTMS-KB-Edit#2026"),
    ("GITHUB_TOKEN", gh_file),
    ("RESEARCH_WORKFLOW_TOKEN", gh_keyring or gh_file),
    ("RESEARCH_WORKFLOW_REF", "master"),
]

failures = []
for name, value in VALUES:
    if not value:
        failures.append(name + ":nilai kosong")
        continue
    result = subprocess.run(
        ["npx", "--no-install", "wrangler", "pages", "secret", "put", name,
         "--project-name", PROJ],
        input=value + "\n", capture_output=True, text=True,
        encoding="utf-8", shell=True, env=env,
    )
    ok = result.returncode == 0
    print(("OK   " if ok else "GAGAL ") + name)
    if not ok:
        tail = (result.stderr or result.stdout or "").strip().splitlines()
        print("   ", tail[-1][:160] if tail else "(tanpa pesan)")
        failures.append(name)

if failures:
    print("SELESAI DENGAN GAGAL:", ", ".join(failures))
    sys.exit(1)
print("SELESAI: 5 secret terpasang.")
