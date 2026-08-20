model: sesi-utama
tiket: E
status: kelar
mulai_wib: 2026-08-18 15:56
selesai_wib: 2026-08-18 16:00
ringkasan:
  Rombak proses.html: 8 kartu paragraf panjang -> timeline bernomor 8 langkah (lingkaran nomor +
  judul + PIC + badge status berwarna selesai=hijau/in-progress=kuning/belum=abu + detail 1 baris)
  alur launch T588 + kartu "Kunci sukses" pendek + kartu latihan Excel ber-bullet (4 soal punya
  poin, angka penting jadi chip 23 total: Rp10.000/jam, Rp15.000/jam, 5%, 2%, Rp700.000, dst).
  proses.json: tambah "langkah" [{urut,judul,pic,status,detail}] 8 item dari fakta "Tahapan New
  Product Launch" (Price List Hendry selesai 3 Agu; Display Plan Sherline selesai 6 Agu; POP Design
  Sherline in-progress tunggu materi HQ; Sellout Program belum; Sell-in Plan Sapto/Hendry/Putri 3
  rencana/channel; Training Material Lidia selesai 6 Agu; Internal Meeting with Sales Sapto jadwal
  7 Agu; PSI Tim minta stok) — field "fakta" LAMA utuh 3 item (search.js/knowledge.js aman).
  tugas.json: tambah "poin" (bullet + penanda [[chip]]) per fakta, "fakta" lama utuh 5 item.
  proses.js (BARU, ES5): renderTimeline + renderTugas, baca window.MTMS_DATA dulu fallback fetch.
  proses.html: renderKb -> renderTimeline + renderTugas, tetap include knowledge.js/search.js.
  style.css: tambah .tl-list/.tl-step/.tl-num/.tl-title/.tl-pic/.tl-detail/.tl-badge(3 warna +
  dark theme)/.chip/.kunci-card/.tugas-poin. Line-height longgar, mobile-first, 390px nol h-scroll.
  verify_proses.py (BARU, pola verify_ringkasan.py, Chrome C:\Program Files\Google\Chrome\Application\chrome.exe):
  '.tl-step' >= 8, paragraf >320 karakter di #konten-proses == 0, 0 console error.
  data.js diregen via gen_data_js.py (37 katalog, 12 knowledge, 7 galeri, 5 files, 6 kompetitor).
  Semua angka dari data proses.json/tugas.json, NOL ngarang. TIDAK deploy/git/hapus.
artifacts:
  - site\data\knowledge\proses.json (tambah "langkah" 8 item, "fakta" 3 item utuh)
  - site\data\knowledge\tugas.json (tambah "poin" 4 soal, "fakta" 5 item utuh)
  - site\js\proses.js (BARU: renderTimeline + renderTugas + chipify + statusBadge, ES5)
  - site\proses.html (renderKb -> renderTimeline/renderTugas, + script proses.js)
  - site\css\style.css (tambah tl-*, .chip, .kunci-card, .tugas-poin + dark theme)
  - tools\verify_proses.py (BARU: 8 step / 0 paragraf panjang / 0 console error)
  - site\js\data.js (diregen via tools\gen_data_js.py)
bukti:
  - a. python -X utf8 -c "import json;d=json.load(open(r'site\data\knowledge\proses.json',encoding='utf-8'));print(len(d['langkah']),len(d['fakta']))" -> 8 3 (PASS)
  - b. python -X utf8 -c "import json;t=json.load(open(r'site\data\knowledge\tugas.json',encoding='utf-8'));print(len(t['fakta']),sum(1 for f in t['fakta'] if 'poin' in f))" -> 5 4 (PASS)
  - c. python -X utf8 tools\gen_data_js.py -> "data.js ditulis OK (37 katalog, 12 knowledge, 7 galeri, 5 files, 6 kompetitor, ringkasan segmen 5)" (PASS)
  - d. python -X utf8 tools\verify_proses.py -> EXIT 0: ".tl-step: 8 (min 8)", "paragraf >320 karakter di #konten-proses: 0", "console error: 0", "verify_proses: LULUS"; isi 8 step terprint: 1 Price List Selesai PIC Hendry | 2 Display Plan Selesai PIC Sherline | 3 POP Design In Progress PIC Sherline | 4 Sellout Program Belum PIC - | 5 Sell-in Plan Belum PIC Sapto/Hendry/Putri | 6 Training Material Selesai PIC Lidia | 7 Internal Meeting with Sales Belum PIC Sapto | 8 PSI Belum PIC Tim (PASS)
  - e. python -X utf8 tools\verify_file_proto.py -> EXIT 0: errors: 0, render_gagal: 0, hscroll: 0, 7 halaman x 2 viewport semua OK termasuk proses.html .card>0 (PASS)
  - f. DOM check headless (playwright file://, 390x844 mobile): chips 23, tugas-card 5, kunci-card 1, badge selesai 3 / in-progress 1 / belum 4, hscroll False, console errors 0 (PASS)
unknowns:
  - Kepatuhan visual (estetika) tidak dinilai mandiri; struktur, data, dan mobile h-scroll terverifikasi DOM headless (390x844 + 1280x800), screenshot tidak diambil tiket ini.
