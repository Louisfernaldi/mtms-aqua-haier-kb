# -*- coding: utf-8 -*-
r"""gen_kompetitor.py — Rakit site\data\kompetitor.json dari riset 6 brand.

Baca (HANYA record found: true):
  D:\AI\projects\kompetitor-haier\komparasi-5brand\data\riset_brand\{AQUA,LG,MIDEA,POLYTRON,SAMSUNG,SHARP}.json

Tulis:
  site\data\kompetitor.json  -> data lama + fondasi spesifikasi dinamis per model

Field per model (angka dari data, NOL ngarang):
  model, subcat (asli), cat (kode kategori), door, capacity_l, price_idr,
  price_source, semua fitur nonempty dari field features, image dari aset lokal
  bila cocok exact atau photo_url, photo_url sebagai provenance, source_url

Pemetaan kategori (subcat di tiap brand beda-beda):
  SD/TM/BM/SBS/MD (AQUA, MIDEA, POLYTRON, SHARP) -> SB/TM/BM/SBS/MD
  LG  "Kulkas 1 Pintu" -> SB; "Kulkas 2 Pintu" -> BM kalau door nyebut Bottom, else TM
  LG  "Kulkas Side by Side" -> SBS; "Kulkas Multi Door" -> MD
  SAMSUNG subcat kosong -> ditebak dari door ("Top Mount Freezer" -> TM)
"""
import json
import os
import re

try:
    from .migrate_dynamic_specs import migrate_document
except ImportError:  # eksekusi langsung: python tools/gen_kompetitor.py
    from migrate_dynamic_specs import migrate_document

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RISET_DIR = r"D:\AI\projects\kompetitor-haier\komparasi-5brand\data\riset_brand"
BRANDS = ["AQUA", "LG", "MIDEA", "POLYTRON", "SAMSUNG", "SHARP"]
PDF_SRC = r"D:\AI\projects\kompetitor-haier\komparasi-5brand\out\KOMPARASI-KULKAS-AQUA-5-BRAND-FINAL-v5.pdf"
MASTER_SRC = r"D:\AI\projects\kompetitor-haier\komparasi-5brand\data\komparasi_master.json"
PDF_DST_NAME = "KOMPARASI-KULKAS-AQUA-5-BRAND-FINAL-v5.pdf"
OUT_JSON = os.path.join(ROOT, "site", "data", "kompetitor.json")
IMAGE_MAP = os.path.join(ROOT, "site", "assets", "kompetitor", "image_map.json")
SPEC_CATEGORIES = os.path.join(ROOT, "site", "data", "spec-categories.json")

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


def normalize_asset_key(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def load_image_index():
    with open(IMAGE_MAP, "r", encoding="utf-8") as fh:
        image_map = json.load(fh)
    index = {}
    for filename, local_path in image_map.items():
        stem = os.path.splitext(os.path.basename(filename))[0]
        key = normalize_asset_key(stem)
        if key and local_path:
            index.setdefault(key, set()).add(local_path)
    return index


def local_image_for(image_index, brand, model):
    matches = image_index.get(normalize_asset_key(str(brand) + str(model)), set())
    if len(matches) == 1:
        return next(iter(matches))
    return None


def load_brand(name, image_index):
    path = os.path.join(RISET_DIR, name + ".json")
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    models = []
    for key, rec in raw.items():
        if not rec.get("found"):
            continue
        features = rec.get("features") or []
        fitur = [f for f in features if str(f).strip()]
        photo_url = rec.get("photo_url")
        models.append({
            "model": key,
            "subcat": rec.get("subcat"),
            "cat": map_cat(rec),
            "door": rec.get("door"),
            "capacity_l": rec.get("capacity_l"),
            "price_idr": rec.get("price_idr"),
            "price_source": rec.get("price_source"),
            "fitur": fitur,
            "image": local_image_for(image_index, name, key) or photo_url,
            "photo_url": photo_url,
            "source_url": rec.get("source_url"),
        })
    return {"brand": name, "model_count": len(models), "models": models}


def load_groups(brands):
    with open(MASTER_SRC, "r", encoding="utf-8") as fh:
        raw_groups = json.load(fh).get("groups", [])
    known = {
        brand["brand"]: {model["model"] for model in brand["models"]}
        for brand in brands
    }
    groups = []
    for raw in raw_groups:
        aqua = raw.get("aqua_base")
        if aqua not in known.get("AQUA", set()):
            continue
        competitors = {}
        for competitor in raw.get("competitors", []):
            brand = str(competitor.get("brand") or "").upper()
            model = competitor.get("model")
            if brand in known and model in known[brand]:
                competitors[brand] = model
        groups.append({"aqua": aqua, "competitors": competitors})
    return groups


def main():
    image_index = load_image_index()
    brands = [load_brand(b, image_index) for b in BRANDS]
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
        "groups": load_groups(brands),
        "sumber": "Riset per brand (website resmi + GFK), lihat price_source per model; angka dihitung mesin dari riset_brand JSON.",
    }
    # Generator tidak boleh menghapus fondasi dynamic specs saat fallback data
    # dibangun ulang. Migrator hanya memakai data lokal hasil generator ini dan
    # tidak meriset atau menebak nilai baru.
    with open(SPEC_CATEGORIES, "r", encoding="utf-8") as fh:
        spec_categories = json.load(fh)
    data = migrate_document(data, spec_categories)
    tmp = OUT_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.replace(tmp, OUT_JSON)
    per = " ".join("%s=%d" % (b["brand"], b["model_count"]) for b in brands)
    print("gen_kompetitor: kompetitor.json ditulis OK (%s, pdf %d bytes)" % (per, pdf_size))


if __name__ == "__main__":
    main()
