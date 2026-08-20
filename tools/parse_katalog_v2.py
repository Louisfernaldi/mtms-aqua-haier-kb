# -*- coding: utf-8 -*-
"""Parse Product Mapping (Ref 2026 Juli) -> katalog.json untuk halaman Produk MTMS.

Versi 2 (Tiket C): menambah field `foto`, `harga_idr`, `harga_source` ke tiap row:
  - foto       : nama file asli di site\\assets\\produk\\ (match nama model,
                 kandidat <model>__0.jpg duluan, lalu <model>__web0.jpg,
                 lalu pola <model>__*.jpg). Model gabungan warna (mis.
                 AQR-DTM265RAP/RAV) dicoba tiap bagian variannya.
  - harga_idr / harga_source: dari AQUA.json (data riset brand). Hanya ditulis
                 kalau model (atau bagian variannya) ada di AQUA.json DAN
                 price_idr terisi; kalau tidak, field TIDAK ditulis (bukan null).
"""
import re, json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, r'tools\extracted\Rotation_-_REF__File_Rapih__AQUA_REF_-_Product_Mapping_(Ref_2026_Juli)_-_Sharleen_MT.xlsx.txt')
OUT = os.path.join(ROOT, r'site\data\produk-katalog.json')
IMG_DIR = os.path.join(ROOT, r'site\assets\produk')
AQUA_JSON = r'D:\AI\projects\kompetitor-haier\komparasi-5brand\data\riset_brand\AQUA.json'

KAT_LABEL = {
    'Single Door (SB)': '1 Pintu',
    'Top Mount (TM)': '2 Pintu Freezer Atas',
    'Bottom Mount (BM)': '2 Pintu Freezer Bawah',
    'Side by Side (SE)': 'Side by Side',
    'Multidoor (TD)': 'Multi Pintu',
}
KAT_GROUP = {
    'Single Door (SB)': 'Single Door',
    'Top Mount (TM)': 'Top Mount',
    'Bottom Mount (BM)': 'Bottom Mount',
    'Side by Side (SE)': 'Side by Side',
    'Multidoor (TD)': 'Multidoor',
}


def kandidat_model(model):
    """Daftar kandidat nama model untuk dicocokkan (utama dulu).

    Model biasa -> [model]. Model gabungan warna (AQR-DTM265RAP/RAV) ->
    bagian pertama + rekonstruksi bagian berikutnya (RAP/RAV -> AQR-DTM265RAV).
    Semua kandidat adalah varian model dasar yang sama, jadi foto/harga
    bagian mana pun sah dipakai (bukan model lain yang menyesatkan).
    """
    if '/' not in model:
        return [model]
    parts = [p for p in model.split('/') if p]
    if not parts:
        return [model]
    out = [parts[0]]
    for p in parts[1:]:
        if p.startswith('AQR-') or p.startswith('AQUA'):
            out.append(p)
        elif len(parts[0]) > 1:
            # varian warna beda huruf terakhir: AQR-DTM265RAP / RAV -> AQR-DTM265RAV
            out.append(parts[0][:-1] + p[-1])
    return out


def cari_foto(model, files):
    """Cari nama file foto untuk satu nama model, atau None."""
    for pat in [model + '__0.jpg', model + '__web0.jpg']:
        if pat in files:
            return pat
    pref = model + '__'
    cands = sorted([f for f in files if f.startswith(pref)])
    return cands[0] if cands else None


def main():
    rows = []
    for line in open(SRC, encoding='utf-8').read().splitlines():
        line = line.strip()
        if not line or line.startswith('===') or line.startswith('Brand |'):
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 7:
            continue
        brand, model, kat, kap, rng, mat, benefit = parts[:7]
        if brand != 'AQUA':
            continue

        m = re.match(r'^(.*?)\s*\((.*)\)\s*$', model)
        if m:
            model_name = m.group(1).strip()
            varian = [v.strip() for v in m.group(2).split('/') if v.strip()]
        else:
            model_name = model
            varian = []

        m2 = re.match(r'^(\d+)\s*\(gross\)\s*/\s*(\d+)\s*\(nett\)$', kap)
        gross = int(m2.group(1)) if m2 else None
        nett = int(m2.group(2)) if m2 else None

        day = None
        m3 = re.search(r'(\d+(?:[.,]\d+)?)\s*W\b', benefit)
        if m3:
            day = m3.group(1).replace(',', '.')

        garansi = None
        m4 = re.search(r'Garansi\s+(?:kompresor\s+)?([A-Za-z ]*?)(\d+)\s*tahun', benefit)
        if m4:
            g = m4.group(2)
            if 'Twin' in m4.group(1):
                g += ' (Twin Inverter)'
            garansi = g

        flags = []
        if 'Twin Inverter' in benefit:
            flags.append('Inverter')
        if 'non-inverter' in benefit.lower():
            flags.append('Non-Inverter')
        if 'Import Thailand' in benefit:
            flags.append('Import Thailand')
        if 'Flagship' in benefit:
            flags.append('Flagship')
        if 'Entry level' in benefit or 'Entry point' in benefit:
            flags.append('Entry')
        if re.search(r'best seller', benefit, re.I):
            flags.append('Best Seller')
        if 'Halo product' in benefit:
            flags.append('Halo Product')

        serie = None
        for s in ['Chic Color Series', 'Magic Neo Series']:
            if s in benefit:
                serie = s.replace(' Series', '')
        if serie is None:
            if 'Smart IoT HaiSmart' in benefit:
                serie = 'HaiSmart'
            elif 'Magic Zone' in benefit:
                serie = 'Magic Zone'

        rows.append({
            'brand': brand,
            'model': model_name,
            'varian': varian,
            'kategori': KAT_LABEL.get(kat, kat),
            'group': KAT_GROUP.get(kat, kat),
            'kapasitas_gross': gross,
            'kapasitas_nett': nett,
            'range': rng,
            'material': mat,
            'daya_watt': day,
            'garansi_tahun': garansi,
            'flags': flags,
            'serie': serie,
            'benefit': benefit,
        })

    # ---- Lampiran Tiket C: foto + harga ----
    files = sorted(os.listdir(IMG_DIR)) if os.path.isdir(IMG_DIR) else []
    aqua = {}
    if os.path.exists(AQUA_JSON):
        aqua = json.load(open(AQUA_JSON, encoding='utf-8'))

    n_foto = 0
    n_harga = 0
    for r in rows:
        foto = None
        for k in kandidat_model(r['model']):
            foto = cari_foto(k, files)
            if foto:
                break
        if foto:
            r['foto'] = 'assets/produk/' + foto
            n_foto += 1

        harga = None
        for k in kandidat_model(r['model']):
            if k in aqua and aqua[k].get('price_idr') is not None:
                harga = aqua[k]
                break
        if harga:
            r['harga_idr'] = int(harga['price_idr'])
            r['harga_source'] = harga['price_source']
            n_harga += 1

    rows.sort(key=lambda r: (r['group'], r['kapasitas_gross'] or 0))
    json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    print('=== REKAP parse_katalog_v2 ===')
    print('total row      :', len(rows))
    print('row dengan foto:', n_foto)
    print('row dengan harga:', n_harga)
    from collections import Counter
    print('grup           :', dict(Counter(r['group'] for r in rows)))
    print('tanpa foto     :', [r['model'] for r in rows if 'foto' not in r])
    print('contoh:', json.dumps(rows[0], ensure_ascii=False)[:400])


if __name__ == '__main__':
    main()
