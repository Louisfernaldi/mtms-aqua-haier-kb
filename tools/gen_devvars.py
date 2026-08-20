# -*- coding: utf-8 -*-
"""Generate .dev.vars (sekali pakai, LOCAL DEV ONLY) dari PAT GitHub di folder kredensial.
File .dev.vars berisi token asli -> WAJIB di-gitignore, jangan pernah commit.
"""
import os

pat = open(os.path.join("D:", os.sep, "Secret", "github api key.txt"), encoding="utf-8").read().strip()
lines = [
    "# LOCAL DEV ONLY - jangan commit (sudah di .gitignore)",
    "GITHUB_TOKEN=" + pat,
    "EDIT_PASSWORD=devtest123",
    "LOGIN_PASSWORD=aquaisthebest",
    "DATA_PATH=produk-katalog-DEV.json",
]
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".dev.vars")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("tulis", os.path.abspath(out))
