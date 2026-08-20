# -*- coding: utf-8 -*-
r"""gen_kompetitor.py — Rakit site\data\kompetitor.json dari riset 6 brand.

Baca (HANYA record found: true):
  D:\AI\projects\kompetitor-haier\komparasi-5brand\data\riset_brand\{AQUA,LG,MIDEA,POLYTRON,SAMSUNG,SHARP}.json

Tulis:
  site\data\kompetitor.json  -> {"pdf": {...}, "brands": [...6...], "categories": [...]}

Field per model (angka dari data, NOL ngarang):
  model, subcat (asli), cat (kode kategori), door, capacity_l, price_idr,
  price_source, fitur (1-2 fitur teratas dari field features), source_url

Pemetaan kategori (subcat di tiap brand beda-beda):
  SD/TM/BM/SBS/MD (AQUA, MIDEA, POLYTRON, SHARP) -> SB/TM/BM/SBS/MD
  LG  "Kulkas 1 Pintu" -> SB; "Kulkas 2 Pintu" -> BM kalau door nyebut Bottom, else TM
  LG  "Kulkas Side by Side" -> SBS; "Kulkas Multi Door" -> MD
  SAMSUNG subcat kosong -> ditebak dari door ("Top Mount Freezer" -> TM)
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RISET_DIR = r"D:\AI\projects\kompetitor-haier\komparasi-5brand\data\riset_brand"
BRANDS = ["AQUA", "LG", "MIDEA", "POLYTRON", "SAMSUNG", "SHARP"]
PDF_SRC = r"D:\AI\projects\kompetitor-haier\komparasi-5brand\out\KOMPARASI-KULKAS-AQUA-5-BRAND-FINAL-v5.pdf"
PDF_DST_NAME = "KOMPARASI-KULKAS-AQUA-5-BRAND-FINAL-v5.pdf"
OUT_JSON = os.path.join(ROOT, "site", "data", "kompetitor.json")

CATEGORIES = [
    {"code": "SB", "label": "1 Pintu", "desc": "Satu pintu, freezer satu ruang"},
    {"code": "TM", "label": "2 Pintu Top Mount", "desc": "Freezer di atas"},
    {"code": "BM", "label": "2 Pintu Freezer Bawah", "desc": "Freezer di bawah"},
    {"code": "SBS", "label": "Side by Side", "desc": "Dua pintu samping"},
    {"code": "MD", "label": "Multi Pintu", "desc": "French Door / lebih dari 2 pintu"},
]


def map_cat(rec):
    sub = str(rec.get("subcat") or "").strip().lower()
    door = str(rec.get("door") or "").lower()
    if sub == "sd":
        return "SB"
    if sub == "tm":
        return "TM"
    if sub == "bm":
        return "BM"
    if sub == "sbs":
        return "SBS"
    if sub == "md":
        return "MD"
    if "side by side" in sub:
        return "SBS"
    if "multi door" in sub or "multidoor" in sub:
        return "MD"
    if "1 pintu" in sub:
        return "SB"
    if "2 pintu" in sub or "dua pintu" in sub:
        if "bottom" in door:
            return "BM"
        return "TM"
    if "top mount" in door:
        return "TM"
    if "bottom mount" in door or "bottom freezer" in door:
        return "BM"
    if "side by side" in door:
        return "SBS"
    if "french door" in door or "multi door" in door or "multidoor" in door:
        return "MD"
    if "1 pintu" in door or "one door" in door:
        return "SB"
    return None


def load_brand(name):
    path = os.path.join(RISET_DIR, name + ".json")
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    models = []
    for key, rec in raw.items():
        if not rec.get("found"):
            continue
        features = rec.get("features") or []
        fitur = [f for f in features if str(f).strip()][:2]
        models.append({
            "model": key,
            "subcat": rec.get("subcat"),
            "cat": map_cat(rec),
            "door": rec.get("door"),
            "capacity_l": rec.get("capacity_l"),
            "price_idr": rec.get("price_idr"),
            "price_source": rec.get("price_source"),
            "fitur": fitur,
            "source_url": rec.get("source_url"),
        })
    return {"brand": name, "model_count": len(models), "models": models}


def main():
    brands = [load_brand(b) for b in BRANDS]
    pdf_size = os.path.getsize(PDF_SRC)
    pdf = {
        "file": PDF_DST_NAME,
        "path": "files/" + PDF_DST_NAME,
        "size_bytes": pdf_size,
        "size_mb": "%.1f MB" % (pdf_size / (1024.0 * 1024.0)),
    }
    data = {
        "pdf": pdf,
        "categories": CATEGORIES,
        "brands": brands,
        "sumber": "Riset per brand (website resmi + GFK), lihat price_source per model; angka dihitung mesin dari riset_brand JSON.",
    }
    tmp = OUT_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, OUT_JSON)
    per = " ".join("%s=%d" % (b["brand"], b["model_count"]) for b in brands)
    print("gen_kompetitor: kompetitor.json ditulis OK (%s, pdf %d bytes)" % (per, pdf_size))


if __name__ == "__main__":
    main()