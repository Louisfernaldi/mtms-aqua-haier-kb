# -*- coding: utf-8 -*-
r"""gen_data_js.py — Embed semua data JSON situs ke site\js\data.js (window.MTMS_DATA).

Baca:
  site\data\produk-katalog.json        -> MTMS_DATA.katalog  (array)
  site\data\knowledge\*.json (12 file) -> MTMS_DATA.knowledge (objek key = nama file json)
  site\data\galeri.json                -> MTMS_DATA.galeri   (array)
  site\data\files.json                 -> MTMS_DATA.files    (array)
  site\data\kompetitor.json            -> MTMS_DATA.kompetitor (objek 6 brand + pdf)

Tulis:
  site\js\data.js  berisi:  window.MTMS_DATA = {katalog:[...], knowledge:{...}, galeri:[...], files:[...], kompetitor:{...}};

Idempoten: output ditulis lewat file sementara lalu direname, konten identik
untuk input yang sama.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "site", "data")
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "knowledge")
OUT_JS = os.path.join(ROOT, "site", "js", "data.js")
PRODUK_DIR = os.path.join(ROOT, "site", "assets", "produk")
RISET_AQUA = r"D:\AI\projects\kompetitor-haier\komparasi-5brand\data\riset_brand\AQUA.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _num(s):
    """Ambil angka awalan dari string (mis. '20 (Twin Inverter)' -> 20, '46.8' -> 46.8)."""
    if s is None:
        return None
    import re
    m = re.match(r"\s*(\d+(?:[.,]\d+)?)", str(s))
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


def build_ringkasan(katalog, knowledge):
    """Hitung angka ringkasan dari JSON (bukan nulis tangan): segmen + stat.

    Sumber: produk-katalog.json (jumlah model, kapasitas, daya, garansi, varian)
    dan segmen_harga di produk-kulkas.json (rentang harga per segmen).
    """
    segmen_order = [
        "Single Door",
        "Top Mount",
        "Bottom Mount",
        "Side by Side",
        "Multidoor",
    ]
    segmen_harga = {}
    if knowledge and knowledge.get("segmen_harga"):
        for sh in knowledge["segmen_harga"]:
            segmen_harga[sh["segmen"]] = sh

    segmen = []
    for g in segmen_order:
        rows = [p for p in katalog if p.get("group") == g]
        caps = [p["kapasitas_gross"] for p in rows if p.get("kapasitas_gross")]
        sh = segmen_harga.get(g, {})
        segmen.append({
            "segmen": g,
            "label": sh.get("label", g),
            "rentang": sh.get("rentang", "-"),
            "sumber": sh.get("sumber", "-"),
            "jumlah_model": len(rows),
            "kapasitas_min": min(caps) if caps else None,
            "kapasitas_max": max(caps) if caps else None,
        })

    garansi = []
    for p in katalog:
        n = _num(p.get("garansi_tahun"))
        if n is not None:
            garansi.append((n, p.get("garansi_tahun"), p.get("model")))
    garansi.sort(key=lambda x: x[0], reverse=True)
    garansi_top = garansi[0] if garansi else (None, None, None)

    daya = []
    for p in katalog:
        n = _num(p.get("daya_watt"))
        if n is not None:
            daya.append((n, p.get("daya_watt"), p.get("model")))
    daya.sort(key=lambda x: x[0])
    daya_top = daya[0] if daya else (None, None, None)
    daya_models = sorted(m for n, w, m in daya if n == daya_top[0])

    stats = {
        "garansi_terpanjang": {
            "nilai": int(garansi_top[0]) if garansi_top[0] is not None else None,
            "label": garansi_top[1],
            "model": garansi_top[2],
        },
        "daya_terhemat": {
            "nilai": daya_top[0] if daya_top[0] is not None else None,
            "label": daya_top[1],
            "models": daya_models,
        },
        "jumlah_model": len(katalog),
        "jumlah_varian": sum(len(p.get("varian") or []) for p in katalog),
    }
    return {"segmen": segmen, "stats": stats, "sumber": "dihitung dari produk-katalog.json + produk-kulkas.json (segmen_harga)"}


def build_foto_list(model, foto):
    """Scan site\\assets\\produk\\ untuk file foto milik model (prefix MODEL__).

    Urutan: __0, __1, __2, ... dulu, __web0 terakhir. Field foto lama (kalau ada)
    dipindah ke posisi pertama foto_list. Nol file + nol foto -> [].
    """
    fotos = []
    if model and os.path.isdir(PRODUK_DIR):
        prefix = model + "__"
        for fn in os.listdir(PRODUK_DIR):
            if fn.lower().startswith(prefix.lower()):
                suf = fn[len(prefix):]
                m = re.match(r"(\d+)\.[^.]*$", suf)
                key = (0, int(m.group(1))) if m else (1, suf.lower())
                fotos.append((key, "assets/produk/" + fn))
        fotos.sort(key=lambda x: x[0])
        fotos = [p for _, p in fotos]
    if foto:
        if foto in fotos:
            fotos.remove(foto)
        fotos.insert(0, foto)
    return fotos


def build_mtms_data():
    katalog = load_json(os.path.join(DATA_DIR, "produk-katalog.json"))
    riset = {}
    if os.path.exists(RISET_AQUA):
        riset = load_json(RISET_AQUA)
    for p in katalog:
        p["foto_list"] = build_foto_list(p.get("model", ""), p.get("foto"))
        feats = []
        if riset and p.get("model") in riset:
            feats = (riset[p["model"]].get("features") or [])[:8]
        p["fitur"] = feats
    galeri = load_json(os.path.join(DATA_DIR, "galeri.json"))
    files = load_json(os.path.join(DATA_DIR, "files.json"))
    kompetitor = load_json(os.path.join(DATA_DIR, "kompetitor.json"))
    knowledge = {}
    for name in sorted(os.listdir(KNOWLEDGE_DIR)):
        if name.endswith(".json"):
            knowledge[name] = load_json(os.path.join(KNOWLEDGE_DIR, name))
    ringkasan = build_ringkasan(katalog, knowledge.get("produk-kulkas.json"))
    return {"katalog": katalog, "knowledge": knowledge, "galeri": galeri, "files": files, "kompetitor": kompetitor, "ringkasan": ringkasan}


def main():
    data = build_mtms_data()
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # Amankan dari penutupan dini tag <script> di HTML (nilai string bisa memuat "</...")
    body = body.replace("</", "<\\/")
    out = (
        "/* DIBANGKITKAN OTOMATIS oleh tools\\gen_data_js.py - JANGAN EDIT MANUAL. */\n"
        "window.MTMS_DATA = " + body + ";\n"
    )
    tmp = OUT_JS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(out)
    if os.path.exists(OUT_JS):
        with open(OUT_JS, "r", encoding="utf-8") as fh:
            if fh.read() == out:
                os.remove(tmp)
                print("gen_data_js: data.js sudah sama, tidak ditulis ulang (idempoten)")
                return
    os.replace(tmp, OUT_JS)
    print("gen_data_js: data.js ditulis OK (%d katalog, %d knowledge, %d galeri, %d files, %d kompetitor, ringkasan segmen %d)" % (
        len(data["katalog"]), len(data["knowledge"]), len(data["galeri"]), len(data["files"]),
        len(data["kompetitor"]["brands"]), len(data["ringkasan"]["segmen"])
    ))


if __name__ == "__main__":
    main()
