model: sesi-utama
tiket: D
status: kelar
mulai_wib: 2026-08-18 15:20
selesai_wib: 2026-08-18 15:47
ringkasan:
  Section "AQUA vs Kompetitor" baru di produk.html SETELAH ringkasan-visual: kartu unduh PDF (nama file + ukuran 1.3 MB + tombol <a download>), 5 chip pilih kategori (1 Pintu SB / 2 Pintu Top Mount TM / 2 Pintu Freezer Bawah BM / Side by Side SBS / Multi Pintu MD), tabel AQUA vs Rata-rata Kompetitor (jumlah model, kapasitas range L, harga min-maks Rp, contoh fitur andalan 2-3 model AQUA dari field features, baris sumber harga official-page/GFK/tanpa-sumber dengan hitungan per label). tools\gen_kompetitor.py (BARU) baca 6 JSON riset_brand (HANYA found:true) -> site\data\kompetitor.json {"brands":[...6...], pdf, categories}; mapping subcat hati-hati (AQUA/MIDEA/POLYTRON/SHARP kode SB/TM/BM/SBS/MD, LG label Indonesia "Kulkas 2 Pintu" dipecah lewat field door Bottom/Top, SAMSUNG 2 record subcat kosong ditebak dari door Top Mount), 0 unmapped. PDF komparasi v5 disalin ke site\files\ (1,405,156 bytes < 25 MiB). kompetitor.js ES5 baca window.MTMS_DATA.kompetitor dulu (regen data.js via gen_data_js.py yang di-extend embed kompetitor), fallback fetch. Semua angka dihitung mesin di browser dari JSON, NOL ngarang. Verifikasi a/b/c LULUS + DOM check headless: pdf_card True, 5 chips, 5 baris tabel, click chip MD -> judul berubah + AQUA count 6 (sesuai data), 0 error console.
artifacts:
  - tools\gen_kompetitor.py (BARU: baca 6 riset_brand JSON -> kompetitor.json, filter found:true, map subcat->SB/TM/BM/SBS/MD, fitur 2 teratas)
  - site\data\kompetitor.json (BARU: 6 brand, 102 model total, pdf + categories)
  - site\files\KOMPARASI-KULKAS-AQUA-5-BRAND-FINAL-v5.pdf (salinan, 1405156 bytes)
  - site\js\kompetitor.js (BARU: renderKompetitor, kartu PDF + chips + tabel, fallback fetch, ES5)
  - site\produk.html (section #konten-kompetitor + h2 setelah ringkasan-visual, script + pemanggil renderKompetitor)
  - site\css\style.css (komp-dl-card/komp-chips/komp-tbl-blok/tbl-scroll/komp-tbl/komp-feat)
  - tools\gen_data_js.py (extend: baca + embed site\data\kompetitor.json -> MTMS_DATA.kompetitor)
  - site\js\data.js (diregen via tools\gen_data_js.py, 37 katalog + 6 kompetitor)
bukti:
  - a. (Get-Item site\files\KOMPARASI-KULKAS-AQUA-5-BRAND-FINAL-v5.pdf).Length -> 1405156 < 26214400 (PASS)
  - b. python -X utf8 -c "import json;d=json.load(open(r'site\data\kompetitor.json',encoding='utf-8'));print(len(d['brands']))" -> 6 (PASS)
  - c. python -X utf8 tools\verify_file_proto.py -> EXIT 0, errors: 0, render_gagal: 0, hscroll: 0, produk .pk-card == 37 di 2 viewport (PASS — katalog & section lain utuh)
  - python -X utf8 tools\gen_kompetitor.py -> "kompetitor.json ditulis OK (AQUA=32 LG=16 MIDEA=7 POLYTRON=13 SAMSUNG=11 SHARP=23, pdf 1405156 bytes)" (PASS)
  - python -X utf8 tools\gen_data_js.py -> "data.js ditulis OK (37 katalog, 12 knowledge, 7 galeri, 5 files, 6 kompetitor, ringkasan segmen 5)" (PASS)
  - cek mapping: 0 unmapped, per-brand subcat -> AQUA {SB:3,TM:18,BM:1,SBS:4,MD:6} LG {SB:2,TM:8,BM:1,SBS:2,MD:3} MIDEA {SB:1,TM:4,SBS:1,MD:1} POLYTRON {SB:3,TM:5,SBS:2,MD:3} SAMSUNG {SB:1,TM:6,BM:1,SBS:1,MD:2} SHARP {SB:6,TM:10,SBS:2,MD:5} (PASS)
  - DOM check headless (playwright file://, 1280x800): pdf_card True, chips 5, rows 5; click chip MD -> title "Multi Pintu — AQUA vs Rata-rata Kompetitor", aqua_count 6; 0 pageerror/console error (PASS)
unknowns:
  - Kepatuhan visual (estetika) tidak dinilai mandiri (model tanpa input gambar); struktur & data terverifikasi via DOM headless, screenshot tidak diambil tiket ini.
  - 5 model tanpa price_idr (LG GN-B392PGFB, LG GN_B222SFIF, MIDEA MDRT385MTB30, SHARP SJ-246SI-GK, AQUA AQR-TTD576RSG) tidak ikut hitung min/maks harga — tetap masuk hitungan jumlah model; label sumber "tanpa sumber" muncul transparan di baris sumber.
