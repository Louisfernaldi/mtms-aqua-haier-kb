# Tiket C — Foto Produk di Katalog (dampak visual terbesar)

Pasang foto asli produk di kartu katalog + modal detail. Sumber: foto kompetitor-haier
AQUA (106 file, 32 model) + metadata harga dari AQUA.json.

```estafet
id: C
status: kelar
depends_on: [B]
owner: subagen-claude-general
verifier: mandor-sesi-utama
file_disentuh:
  - tools\parse_katalog_v2.py
  - site\assets\produk
  - site\data\produk-katalog.json
  - site\js\produk.js
  - site\js\data.js
  - tools\gen_data_js.py
  - site\css\style.css
file_dibaca_doang:
  - tools\verify_file_proto.py
cek_selesai:
  - "(Get-ChildItem D:\\AI\\projects\\mtms-aqua-haier-kb\\site\\assets\\produk -File).Count -> >= 100"
  - "python -X utf8 -c \"import json;d=json.load(open(r'D:\\AI\\projects\\mtms-aqua-haier-kb\\site\\data\\produk-katalog.json',encoding='utf-8'));print(sum(1 for r in d if r.get('foto')))\" -> >= 30"
  - "python -X utf8 D:\\AI\\projects\\mtms-aqua-haier-kb\\tools\\verify_file_proto.py -> exit 0, errors: 0"
gerbang_acc:
```

## Detail
- Copy `D:\AI\projects\kompetitor-haier\komparasi-5brand\images\AQUA\*` (106 jpg) → `site\assets\produk\`.
- `tools\parse_katalog_v2.py` (extend dari `D:\AI\tmp\win-temp\opencode\parse_katalog.py`): tambah field `foto` (match model dasar, pola `AQR-350RBG__0.jpg` — prioritize `__0.jpg` daripada `__web0.jpg`; varian warna pakai foto model dasar, JANGAN foto model lain menyesatkan) + `harga_idr` + `harga_source` (match key AQUA.json `D:\AI\projects\kompetitor-haier\komparasi-5brand\data\riset_brand\AQUA.json`, 32 model).
- UI `produk.js` + `style.css`: thumbnail di kartu (rasio 4:3 tetap, object-fit: cover, loading=lazy, alt = nama model) + foto besar di modal (atas tabel). Model tanpa foto → placeholder ikon kulkas (SVG/emoji), BUKAN foto model lain.
- Regenerasi `site\js\data.js` via `tools\gen_data_js.py`.
- Harga tampil di kartu/modal dengan format `Rp 9.657.000` + label sumber (official-page/GFK).
