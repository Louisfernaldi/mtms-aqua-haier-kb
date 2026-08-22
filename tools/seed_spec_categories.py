# -*- coding: utf-8 -*-
"""Seed spec-categories.json ke repo data produksi (create-only, idempoten).

Editor spesifikasi live mati (GH_READ_404) karena berkas registry kategori
belum pernah diunggah ke repo data. Isi = salinan persis site/data lokal
(sudah memuat keputusan owner: door_count & freezer_position non-tabel).
"""
import base64
import json
import os

REPO = "Louisfernaldi/mtms-aqua-haier-kb-data"
LOCAL = os.path.join("site", "data", "spec-categories.json")

payload = open(LOCAL, "rb").read()
json.loads(payload.decode("utf-8"))  # validasi sebelum naik
content = base64.b64encode(payload).decode("ascii")
body = {
    "message": "seed spec-categories (registry kategori global)",
    "content": content,
    "branch": "main",
}
open(os.path.join(os.environ.get("TEMP", "."), "_seed_body.json"), "w").write(json.dumps(body))
print("body siap:", len(payload), "bytes")
