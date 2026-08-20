# -*- coding: utf-8 -*-
"""Set Pages secret via wrangler (nilai dari stdin atau file). Cuma buat yang punya izin.
Usage:
  python tools/wr_secret.py NAME < value.txt
"""
import os, subprocess, sys
tok = open(os.path.join("D:", os.sep, "Secret", "cloudflare-pages-token.txt"), encoding="utf-8").read().strip()
val = sys.stdin.read().strip()
env = dict(os.environ); env["CLOUDFLARE_API_TOKEN"] = tok
name = sys.argv[1]
cmd = f"npx --no-install wrangler pages secret put {name}"
print(">>>", cmd)
r = subprocess.run(cmd, input=val, env=env, shell=True, capture_output=True, text=True, timeout=120)
print(r.stdout[-1500:])
print("RC", r.returncode)
