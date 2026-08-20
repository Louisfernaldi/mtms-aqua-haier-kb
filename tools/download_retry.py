import sys
import io
import re
import os
import time
import traceback
import requests
import gdown

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = "https://drive.google.com/drive/folders/1gRsY6VlPw2sj8XXFxS1M0sK1DEEGPm5k"
BASE = r"D:\AI\projects\mtms-aqua-haier-kb\materi-drive"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA})

def is_html(r):
    return "html" in r.headers.get("Content-Type", "").lower()

def save(r, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        for chunk in r.iter_content(65536):
            if chunk:
                f.write(chunk)
    os.replace(tmp, path)

def download_uc(fid, path, confirm=None):
    url = f"https://drive.google.com/uc?id={fid}&export=download"
    if confirm:
        url += f"&confirm={confirm}"
    r = S.get(url, timeout=60, allow_redirects=True)
    if r.status_code != 200 or is_html(r):
        raise RuntimeError(f"uc failed HTTP {r.status_code}")
    save(r, path)
    return path

def export_sheet(fid, path):
    for fmt, ext in (("xlsx", ".xlsx"), ("csv", ".csv")):
        r = S.get(f"https://docs.google.com/spreadsheets/d/{fid}/export?format={fmt}", timeout=120)
        if r.status_code == 200 and not is_html(r) and len(r.content) > 200:
            out = path if path.lower().endswith(ext) else path + ext
            save(r, out)
            return out
    raise RuntimeError("sheet export failed")

def export_doc(fid, path):
    r = S.get(f"https://docs.google.com/document/d/{fid}/export?format=docx", timeout=120)
    if r.status_code == 200 and not is_html(r) and len(r.content) > 200:
        out = path if path.lower().endswith(".docx") else path + ".docx"
        save(r, out)
        return out
    raise RuntimeError("doc export failed")

FAILED = {
    "Product Knowledge/CC Catalog": "1LWkWpZ7xpIFvOZ72HWAXD3tXX3Ia2j7K",
    "Product Knowledge/CC Product For Onboarding 2026.pdf": "16OqLw850tm7-znO82LajhU4GosFG1C8N",
    "Rotation - REF/File Rapih/Aqua PM": "1Ng1vo5qDKsd55WvEmiGOnOXgx6O-zCH8QGW7s2tbEDo",
    "Rotation - REF/File Rapih/AQUA REF - Product Mapping (Ref 2026 Juli) - Sharleen MT": "1nP-qimRulIoJ9n1eviLG9LyUQBwvOzzJGUvVXK0Iuxk",
    "Rotation - REF/Aqua PM": "1SCdELm1xrEvxx8kpVjnAsEjqy_Fk20pE3Dq3ogGYFPQ",
    "Rotation - REF/Bandingin Produk": "11Czlu30rzacGnANSSowFnnMj883i7ZfNG7te8MdIRuE",
    "Rotation - REF/Benchmark_Kulkas_Indonesia_Agu2026": "1m6GqpTXWIpAMyYSoxhY_9mgWQAzTUBQ4NNxa8P0xboA",
    "Rotation - REF/Diagram Sebar - Kapasitas vs Kategori (AQUA vs Kompetitor) - Sharleen MT": "1EauuFVrPoWPZlIAqUkgTEWTfCSCEKQv2P9EayicPJdo",
    "Rotation - REF/GFK_STDB_COOLING_ID_HAIERASIAINTERNATI_Jun25": "1IKxquaXreyK9P5rd5l7LnGpVs9nXL9H4poQ-RrzMFmE",
    "Rotation - REF/Product Mapping REF 2026 - AQUA vs Sharp, Midea, Polytron - Sharleen MT": "1r91kDVkZJ0s-5Ra1CXZX1Ln1YWT8VawLRaG_NX6zSz0",
    "Rotation - REF/Product mapping-REF": "1iymEieIs788kgoGpASLKqfZqKjRbUNiAKJh_4K-XpqI",
    "Rotation - REF/Product_Benchmark_rev_Agu2026 (1)": "1Z6_FYEa2qdIl0jbzuTlyS2yKhl8PTsxRoFgrRahq-E0",
    "Rotation - REF/REF_SM": "1Xo0dUowE59veJt54Gm4ik4ox8muRRrYDEtA0kcaKcqM",
    "Rotation - REF/REF_SM_feedback": "1ZMhIOV9rqaxfkm9cOTOOnLkpeagh_OcVpWc977JieWA",
    "Rotation - REF/T588新品推广进度": "1lIhC_NeqAG72VIkSi6_2HIKmk695MksG2wtjk8NlbOc",
}

def main():
    # build path -> id map from listing to keep exact local paths
    files = gdown.download_folder(ROOT, output=BASE, skip_download=True, quiet=True)
    path_by_id = {f.id: f.local_path for f in files}
    ok, fail = [], []
    for rel, fid in FAILED.items():
        path = path_by_id.get(fid, os.path.join(BASE, rel))
        try:
            # 1) try sheet export (most likely)
            out = export_sheet(fid, path)
            print(f"OK  (sheet) {rel} -> {os.path.basename(out)}", flush=True)
            ok.append(rel)
            continue
        except Exception as e1:
            pass
        try:
            out = export_doc(fid, path)
            print(f"OK  (doc)   {rel}", flush=True)
            ok.append(rel)
            continue
        except Exception:
            pass
        # 2) try resolving shortcut via /open
        try:
            r = S.get(f"https://drive.google.com/open?id={fid}", timeout=60, allow_redirects=True)
            m = re.search(r"file/d/([A-Za-z0-9_-]{20,})/view", r.url)
            if m:
                out = download_uc(m.group(1), path)
                print(f"OK  (shortcut->file) {rel}", flush=True)
                ok.append(rel)
                continue
            m2 = re.search(r"folders/([A-Za-z0-9_-]{20,})", r.url)
            if m2:
                print(f"SKIP (points-to-folder) {rel}", flush=True)
                fail.append((rel, "folder-shortcut"))
                continue
            print(f"FAIL {rel}: open-resolve no target ({r.url[:100]})", flush=True)
            fail.append((rel, "open-no-target"))
        except Exception as e:
            print(f"FAIL {rel}: {str(e)[:150]}", flush=True)
            fail.append((rel, str(e)[:150]))
        time.sleep(0.5)
    print(f"\n=== RETRY RESULT: ok={len(ok)} fail={len(fail)} ===", flush=True)
    for rel, err in fail:
        print(f"STILL-FAILED: {rel} :: {err}", flush=True)
    return 0 if not fail else 1

if __name__ == "__main__":
    sys.exit(main())