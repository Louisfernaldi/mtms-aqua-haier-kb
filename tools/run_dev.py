# -*- coding: utf-8 -*-
"""Jalankan wrangler pages dev + subcommand, lalu bunuh SELURUH pohon proses (anti-zombie).
Usage:
    python tools/run_dev.py <port> -- <perintah yang dijalankan>
Contoh:
    python tools/run_dev.py 8790 -- python -X utf8 tools/_e2e_full.py
"""
import os, subprocess, sys, time, socket, urllib.request

PORT = sys.argv[1]
i = sys.argv.index("--")
cmd = sys.argv[i + 1:]
token = open(os.path.join("D:", os.sep, "Secret", "cloudflare-pages-token.txt"), encoding="utf-8").read().strip()
env = dict(os.environ)
env["CLOUDFLARE_API_TOKEN"] = token
env["PORT"] = PORT

dev = subprocess.Popen(
    "npx --no-install wrangler pages dev site --port " + PORT,
    env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True,
)

def ready():
    for _ in range(60):
        if dev.poll() is not None:
            return False
        try:
            s = socket.create_connection(("127.0.0.1", int(PORT)), timeout=1)
            s.close()
            return True
        except OSError:
            time.sleep(1)
    return False

ok = ready()
if not ok:
    print("dev server tidak siap / mati")
    rc = 1
else:
    print("dev server siap di", PORT)
    rc = subprocess.run(cmd, cwd=os.getcwd(), env=env).returncode

# bunuh seluruh pohon (dev + anak-anaknya)
subprocess.run(["taskkill", "/PID", str(dev.pid), "/T", "/F"], capture_output=True)
time.sleep(1)
sys.exit(rc)