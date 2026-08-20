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
H = {"User-Agent": UA}
S = requests.Session()
S.headers.update(H)

def http_get(url, timeout=60, stream=False):
    return S.get(url, timeout=timeout, stream=stream, allow_redirects=True)

def save_stream(r, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        for chunk in r.iter_content(65536):
            if chunk:
                f.write(chunk)
    os.replace(tmp, path)

def is_html(r):
    ct = r.headers.get("Content-Type", "")
    return "html" in ct.lower()

def download_file(fid, path, retries=2):
    url = f"https://drive.google.com/uc?id={fid}&export=download"
    r = http_get(url)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    if is_html(r):
        text = r.text
        low = text.lower()
        # virus-scan confirmation page
        m = re.search(r'name="confirm" value="([0-9A-Za-z_-]+)"', text)
        if m and "virus" in low:
            url2 = f"https://drive.google.com/uc?id={fid}&export=download&confirm={m.group(1)}"
            r2 = http_get(url2)
            if r2.status_code != 200 or is_html(r2):
                raise RuntimeError("confirm-follow failed")
            save_stream(r2, path)
            return
        # Google Docs / Sheets / Slides export
        if "spreadsheets" in low or "docs.google.com/spreadsheets" in low or "google spreadsheets" in low:
            r3 = http_get(f"https://docs.google.com/spreadsheets/d/{fid}/export?format=xlsx")
            if r3.status_code == 200 and not is_html(r3) and len(r3.content) > 1000:
                save_stream(r3, path if path.lower().endswith(".xlsx") else path + ".xlsx")
                return
            raise RuntimeError("sheet-export failed")
        if "document" in low and "docs.google.com/document" in low:
            r4 = http_get(f"https://docs.google.com/document/d/{fid}/export?format=docx")
            if r4.status_code == 200 and not is_html(r4) and len(r4.content) > 1000:
                save_stream(r4, path if path.lower().endswith(".docx") else path + ".docx")
                return
            raise RuntimeError("doc-export failed")
        # drive.google.com page (shortcut to folder/file) -> follow uc redirect again
        m2 = re.search(r'"([^"]{10,})"' , text)
        if "drive.google.com/drive/folders" in text:
            raise RuntimeError("points-to-folder")
        raise RuntimeError("html-unknown: " + re.sub(r"\s+", " ", text[:120]))
    save_stream(r, path)

def main():
    print("=== LISTING ===", flush=True)
    files = gdown.download_folder(ROOT, output=BASE, skip_download=True, quiet=True)
    print(f"LISTED {len(files)} files", flush=True)
    ok, fail, skip = [], [], []
    for i, f in enumerate(files, 1):
        path = f.local_path
        if path and path.lower().endswith(".lnk"):
            skip.append((f.id, f.path))
            print(f"[{i}/{len(files)}] SKIP lnk {f.path}", flush=True)
            continue
        try:
            download_file(f.id, path)
            ok.append(path)
            print(f"[{i}/{len(files)}] OK  {f.path}", flush=True)
        except Exception as e:
            fail.append((f.id, f.path, str(e)[:150]))
            print(f"[{i}/{len(files)}] FAIL {f.path}: {str(e)[:120]}", flush=True)
        time.sleep(0.3)
    print(f"\n=== RESULT: ok={len(ok)} fail={len(fail)} skip={len(skip)} ===", flush=True)
    for fid, path, err in fail:
        print(f"FAILED: {path} (id={fid}) :: {err}", flush=True)
    return 0 if not fail else 1

if __name__ == "__main__":
    sys.exit(main())