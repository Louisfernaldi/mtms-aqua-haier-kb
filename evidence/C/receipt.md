tiket: C
status: selesai
ringkasan:
  model: opencode-go/deepseek-v4-flash
  Foto produk terpasang di kartu katalog + modal (37 kartu, 27 dapat foto asli), harga pasar tampil di kartu & modal dari AQUA.json (23 row), placeholder emoji kulkas untuk 10 row tanpa foto. Parser lama diperluas jadi tools\parse_katalog_v2.py (tambah field foto/harga_idr/harga_source), katalog diregen, data.js diregen (embed 27 referensi foto), UI produk.js + style.css. Semua verifikasi hijau kecuali target foto >= 30: data sumber hanya mendukung 27 (10 row nol file foto cocok di folder AQUA; memakai foto model lain dilarang tiket — "JANGAN foto model lain menyesatkan").
next_actions:
  - Target cek "row dengan foto >= 30" tidak tercapai (27) karena keterbatasan sumber: 10 row (AQR-320RBG, AQR-CTD506RBG, AQR-CTD506RBC, AQR-TSE696RAV, AQR-DTM248CBP x2, AQR-DTM268CBP x2, AQR-DTM288CBP x2) tidak punya file foto nama model di D:\AI\projects\kompetitor-haier\komparasi-5brand\images\AQUA\. Tidak difabrikasi (larangan tiket). Kalau mandor mau 30+, perlu sumber foto tambahan.
  - Model gabungan warna (AQR-DTM265RAP/RAV dkk) difoto pakai varian pertama yang ada (bukan model lain) — sudah masuk 27.
artifacts:
  - tools\parse_katalog_v2.py (parser baru, tambah foto+harga)
  - site\assets\produk\ (106 jpg disalin, nama persis)
  - site\data\produk-katalog.json (37 row, +foto/+harga_idr/+harga_source)
  - site\js\produk.js (thumbnail kartu, harga kartu, foto besar modal, baris Harga pasar)
  - site\js\data.js (regen via tools\gen_data_js.py, 27 referensi foto ter-embed)
  - site\css\style.css (pk-thumb/pk-noimg/pk-price/pk-modal-img/pk-harga-src)
bukti:
  - (Get-ChildItem site\assets\produk -File).Count -> 106 (>= 100 PASS)
  - python -X utf8 -c "...sum(1 for r in d if r.get('foto'))" -> 27 (target >= 30 TIDAK tercapai, alasan di next_actions)
  - python -X utf8 tools\verify_file_proto.py -> exit 0, errors: 0, render_gagal: 0, produk .pk-card == 37 (PASS)
  - python -X utf8 tools\parse_katalog_v2.py -> total row: 37, row dengan foto: 27, row dengan harga: 23
  - node --check site\js\produk.js dan site\js\data.js -> OK
  - 0 file foto missing (semua path assets/produk/ yang direferensikan ada)
unknowns:
  - Tidak ada field foto untuk 10 row (dibuat placeholder ❄️ di UI sesuai spesifikasi, bukan foto model lain)
  - AQUA.json punya 2 model (AQR-TTD576RSG) dengan price_idr null -> field harga tidak ditulis (sesuai "jangan null palsu")
