model: sesi-utama
tiket: F
status: kelar
mulai_wib: 2026-08-18 15:12
selesai_wib: 2026-08-18 15:33
ringkasan:
  Section "Ringkasan Pengetahuan" produk.html (13 kartu paragraf renderKb) dirombak jadi visual <section id="ringkasan-visual">: tabel segmen harga 5 baris (Single Door/Top Mount/Bottom Mount/Side by Side/Multidoor) dengan kolom Segmen | Rentang Harga (Rp) | Jumlah Model | Kapasitas Range + 4 stat-card (garansi kompresor terpanjang 20 th, daya terhemat 33 W, jumlah model 37, jumlah varian 69) + 4 kartu bullet pendek dari fakta (Seri AQR-D, Keunggulan seri AQR-D, Analisa segmen, Model unggulan MD). Semua angka dihitung MESIN: tools\gen_data_js.py di-extend (build_ringkasan) menghitung dari produk-katalog.json + segmen_harga di produk-kulkas.json, hasil di-embed ke site\js\data.js sebagai MTMS_DATA.ringkasan; produk.js renderRingkasan membaca itu (ada fallback hitung-di-browser kalau data.js lama). Rentang harga per segmen diambil verbatim dari blok segmen_harga yang ditambah ke produk-kulkas.json (sumber fakta "Rentang harga per segmen", Aqua PM) — field "fakta" DI-PERTAHANKAN penuh (search.js & renderKb halaman lain tetap aman, terverifikasi cuma baca j.fakta). Fakta produk-lain.json (dispenser/AC/TV/mesin cuci) tetap tampil via renderKb di div konten-produk-lain. Urutan section: ringkasan-visual -> produk-lain -> katalog (ringkasan sebelum katalog sesuai brief). 1 bug ditemukan & difix selama kerja: generator awal pakai variabel loop sisa (p) di generator expression daya_models -> model daya terhemat salah (VTM535RAG) -> diperbaiki pakai m dari tuple, data.js diregen, verifikasi ulang LULUS.
artifacts:
  - site\produk.html (section ringkasan-visual baru sebelum katalog; konten-produk diganti konten-produk-lain; inline script renderRingkasan)
  - site\js\produk.js (fungsi renderRingkasan + hitungRingkasan fallback; renderKatalog tidak disentuh)
  - site\css\style.css (ringkasan-blok/judul/stats/stat-card/bullets/rk-bullets/rk-sumber)
  - site\data\knowledge\produk-kulkas.json (blok segmen_harga 5 segmen, field fakta utuh)
  - tools\gen_data_js.py (build_ringkasan: segmen+stats dihitung mesin, embed MTMS_DATA.ringkasan)
  - tools\verify_ringkasan.py (BARU: playwright headless file://, cek >=5 baris tabel, >=4 stat-card, 0 console error, print semua angka)
  - site\js\data.js (diregen via tools\gen_data_js.py, 37 katalog + ringkasan)
bukti:
  - python -X utf8 tools\gen_data_js.py -> "data.js ditulis OK (37 katalog, 12 knowledge, 7 galeri, 5 files, ringkasan segmen 5)" (PASS)
  - node --check site\js\produk.js dan site\js\data.js -> OK (PASS)
  - python -X utf8 tools\verify_ringkasan.py -> EXIT 0: baris tabel = 5 (>=5 PASS), stat-card = 4 (>=4 PASS), console error = 0 (PASS). Isi tabel: Single Door 6 model 185-225L | Top Mount 15 model 248-535L | Bottom Mount 3 model 320-350L | Side by Side 5 model 565-696L | Multidoor 8 model 506-746L. Stat: 20 th garansi terpanjang, 33 W daya terhemat (AQR-CTD506RBC/RBG), 37 model, 69 varian.
  - python -X utf8 tools\verify_file_proto.py -> EXIT 0, errors: 0, render_gagal: 0, hscroll: 0, produk .pk-card == 37 di 2 viewport (PASS — katalog & foto tetap utuh)
  - python -X utf8 -c (debug daya_terhemat) -> min 33.0 model [AQR-CTD506RBG, AQR-CTD506RBC] (PASS, angka dari JSON bukan tangan)
  - Select-String search.js/knowledge.js -> cuma baca j.fakta, key segmen_harga tidak dipakai (PASS, halaman lain aman)
  - Screenshot section: D:\AI\tmp\win-temp\opencode\ringkasan-f.png (verifikasi visual manual; model sesi ini tidak bisa baca gambar, cek struktural via DOM di atas)
unknowns:
  - Kepatuhan visual (estetika) tidak bisa dinilai sendiri oleh model ini (tidak mendukung input gambar); struktur & data terverifikasi via DOM. Screenshot tersedia untuk mandor.
  - Sumber rentang harga adalah fakta "Rentang harga per segmen" (Aqua PM) yang tidak memisahkan Top Mount vs Bottom Mount (satu baris "2 pintu inverter: 3-6 juta") — keduanya diberi rentang sama 3-6 juta sesuai sumber, bukan ditebak beda.