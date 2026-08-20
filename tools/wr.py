# -*- coding: utf-8 -*-
"""Runner wrangler dengan token Cloudflare (baca dari folder kredensial, jangan di-commit).

Usage:
    python tools/wr.py kv namespace create mtms-produk
    python tools/wr.py kv key put --binding=MTMS_PRODUK 'produk:v1' --path=file.json
    python tools/wr.py pages secret put EDIT_PASSWORD
    python tools/wr.py pages deploy site --project-name mtms-aqua-haier-kb --branch master
"""
import os
import subprocess
import sys

SECRET_TOKEN = os.path.join("D:", os.sep, "Secret", "cloudflare-pages-token.txt")


def main():
    if not os.path.exists(SECRET_TOKEN):
        print("FATAL: token tidak ditemukan:", SECRET_TOKEN)
        sys.exit(2)
    token = open(SECRET_TOKEN, encoding="utf-8").read().strip()
    if not token:
        print("FATAL: token kosong")
        sys.exit(2)
    env = dict(os.environ)
    env["CLOUDFLARE_API_TOKEN"] = token
    cmd = "npx --no-install wrangler " + " ".join(sys.argv[1:])
    print(">>>", cmd)
    r = subprocess.run(cmd, env=env, shell=True)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
