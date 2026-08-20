# -*- coding: utf-8 -*-
"""Deploy situs MTMS AQUA HAIER Knowledge Hub ke Cloudflare Pages (branch master = alias live).

Baca token dari D:\\Secret\\cloudflare-pages-token.txt (folder kredensial — jangan di-commit).
Usage:
    python tools/deploy_pages.py [--branch master]
Default branch = master (alias live resmi). Tanpa branch, wrangler mengirim ke production/main
yang TIDAK tampil di alias master (pelajaran Tiket H4-H8).
"""
import os
import subprocess
import sys

SECRET_TOKEN = os.path.join("D:", os.sep, "Secret", "cloudflare-pages-token.txt")
PROJECT = "mtms-aqua-haier-kb"
DIR = "site"


def main():
    branch = "master"
    if "--branch" in sys.argv:
        i = sys.argv.index("--branch")
        if i + 1 < len(sys.argv):
            branch = sys.argv[i + 1]

    if not os.path.exists(SECRET_TOKEN):
        print("FATAL: token tidak ditemukan:", SECRET_TOKEN)
        sys.exit(2)
    token = open(SECRET_TOKEN, encoding="utf-8").read().strip()
    if not token:
        print("FATAL: token kosong")
        sys.exit(2)

    env = dict(os.environ)
    env["CLOUDFLARE_API_TOKEN"] = token

    cmd = "npx --no-install wrangler pages deploy {dir} --project-name {proj} --branch {branch}".format(
        dir=DIR, proj=PROJECT, branch=branch)
    print(">>>", cmd)
    r = subprocess.run(cmd, env=env, shell=True)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
