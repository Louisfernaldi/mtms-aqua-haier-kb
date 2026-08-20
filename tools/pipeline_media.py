import sys
import io
import os
import shutil
from PIL import Image
from pillow_heif import register_heif_opener

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
register_heif_opener()

BASE = r"D:\AI\projects\mtms-aqua-haier-kb\materi-drive"
WEB = r"D:\AI\projects\mtms-aqua-haier-kb\site\media"

def main():
    stats = {"heic": 0, "renamed": 0, "skipped": 0}
    for root, dirs, fns in os.walk(BASE):
        rel_dir = os.path.relpath(root, BASE)
        for fn in fns:
            src = os.path.join(root, fn)
            lower = fn.lower()
            # 1) HEIC -> JPG
            if lower.endswith(".heic"):
                out_dir = os.path.join(WEB, rel_dir)
                os.makedirs(out_dir, exist_ok=True)
                out = os.path.join(out_dir, fn.rsplit(".", 1)[0] + ".jpg")
                if not os.path.exists(out):
                    im = Image.open(src)
                    im = im.convert("RGB")
                    im.save(out, "JPEG", quality=88)
                stats["heic"] += 1
                continue
            # 2) file tanpa ekstensi yang ternyata PDF
            if "." not in fn:
                with open(src, "rb") as f:
                    magic = f.read(5)
                if magic == b"%PDF-":
                    newname = fn + ".pdf"
                    newpath = os.path.join(root, newname)
                    if not os.path.exists(newpath):
                        os.rename(src, newpath)
                    stats["renamed"] += 1
                    src = newpath
                    fn = newname
            # 3) salin file lain (jpg/png/pdf/docx/xlsx/xlsb) ke WEB
            ext = fn.lower().rsplit(".", 1)[-1]
            if ext in ("jpg", "jpeg", "png", "webp"):
                out_dir = os.path.join(WEB, rel_dir)
                os.makedirs(out_dir, exist_ok=True)
                out = os.path.join(out_dir, fn)
                if not os.path.exists(out):
                    shutil.copy2(src, out)
                stats["skipped"] += 1
    print(f"done: {stats}")

if __name__ == "__main__":
    main()