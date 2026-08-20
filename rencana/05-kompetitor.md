# Tiket D — Section "AQUA vs Kompetitor" + PDF Pembanding

Louis: "yg udah dibuat pdfnya sebelumnya". Data 6 brand siap pakai + PDF final komparasi
5 brand → section baru di produk.html + tombol unduh.

```estafet
id: D
status: kelar
depends_on: [F]
owner: subagen-claude-general
verifier: mandor-sesi-utama
file_disentuh:
  - tools\gen_kompetitor.py
  - site\data\kompetitor.json
  - site\js\kompetitor.js
  - site\produk.html
  - site\css\style.css
  - site\files\KOMPARASI-KULKAS-AQUA-5-BRAND-FINAL-v5.pdf
  - tools\gen_data_js.py
  - site\js\data.js
file_dibaca_doang:
  - tools\verify_file_proto.py
cek_selesai:
  - "(Get-Item D:\\AI\\projects\\mtms-aqua-haier-kb\\site\\files\\KOMPARASI-KULKAS-AQUA-5-BRAND-FINAL-v5.pdf).Length -> < 26214400 (25 MiB)"
  - "python -X utf8 -c \"import json;d=json.load(open(r'D:\\AI\\projects\\mtms-aqua-haier-kb\\site\\data\\kompetitor.json',encoding='utf-8'));print(len(d['brands']))\" -> == 6"
  - "python -X utf8 D:\\AI\\projects\\mtms-aqua-haier-kb\\tools\\verify_file_proto.py -> exit 0, errors: 0"
gerbang_acc:
```

## Detail
- `tools\gen_kompetitor.py`: baca `D:\AI\projects\kompetitor-haier\komparasi-5brand\data\riset_brand\{AQUA,LG,MIDEA,POLYTRON,SAMSUNG,SHARP}.json` → `site\data\kompetitor.json` (per brand: jumlah model, daftar model {model, subcat, capacity_l, price_idr, fitur andalan 1-2, source_url}). Hanya record `found: true`. Angka dari data, NOL ngarang.
- Copy `D:\AI\projects\kompetitor-haier\komparasi-5brand\out\KOMPARASI-KULKAS-AQUA-5-BRAND-FINAL-v5.pdf` → `site\files\` + verifikasi <25 MiB.
- `site\js\kompetitor.js`: render section "AQUA vs Kompetitor" SETELAH ringkasan-visual di produk.html: (1) kartu PDF unduh (nama + ukuran MB + tombol), (2) tabel per-kategori (SB/TM/BM/SBS/MD — pakai label manusia "1 Pintu/2 Pintu Freezer Atas/..."): AQUA vs rata-rata kompetitor — kapasitas, harga min-maks, jumlah model, contoh fitur andalan; sumber ditandai per baris (official-page/GFK), (3) dropdown/chip pilih kategori biar interaktif, mobile-friendly (tabel scroll-x container).
- Data source utama `window.MTMS_DATA.kompetitor` (regen data.js), fallback fetch.
