# Audit A2 — produk.html & proses.html (18 Agu 2026, 13.00 WIB)

Target LIVE: `https://master.mtms-aqua-haier-kb.pages.dev/produk.html` dan `.../proses.html` (branch master).
Sifat: BASELINE ANGKA pra-rombak. Semua klaim di bawah = hasil ukur headless atau hitung berkas lokal (path disebut).

## Metode

- Headless Chrome via Python Playwright (async), executable `C:\Program Files\Google\Chrome\Application\chrome.exe`.
- 2 viewport per halaman: desktop 1280x800 dan mobile 390x844; `wait_until=networkidle` + tunggu 600 ms.
- Metrik DOM: console error/pageerror, h-scroll (`scrollWidth > clientWidth+1`), img broken (`naturalWidth===0`) & tanpa-alt, jumlah elemen (`.pk-card`, `.pk-chip`, `.card`), panjang `textContent` paragraf kartu, computed font-size terkecil di `<main>`, uji klik kartu → modal.
- Script: `D:\AI\tmp\win-temp\opencode\audit_a2.py` · output mentah JSON: `D:\AI\tmp\win-temp\opencode\audit_a2_out.json` (4 run: 2 halaman x 2 viewport, hasil desktop/mobile identik untuk semua metrik).
- Pembanding materi: 4 ekstrak teks di `tools\extracted\` (semua <5 MB; file >5 MB di-skip sesuai instruksi).
- Pemeriksaan data lokal: `site\data\produk-katalog.json` (37 item), `site\data\knowledge\{produk-kulkas,produk-lain,proses,tugas}.json`, `site\js\produk.js`, `site\js\knowledge.js`.

## produk.html

| Prioritas | Temuan | Bukti angka (hasil ukur) | Saran (baseline → target) |
|---|---|---|---|
| P1 | Kartu katalog TIDAK punya foto — konfirmasi keluhan owner. 37 kartu, 0 `<img>`; data JSON juga 0/37 punya field gambar; fungsi `card()` di `produk.js:61-84` memang tidak pernah merender `<img>` | `pk_cards=37`, `pk_img_in_card=0`, satu-satunya img di halaman = 1 (logo Haier header); field gambar di `produk-katalog.json` = 0 dari 37 item | Tambah field `img` per item (37/37) + elemen `<img>` di kartu + placeholder SVG saat foto belum ada. **Baseline: 0 img → target 37.** Modal (detail) juga 0 img — pertimbangkan foto besar di modal |
| P2 | Section "Ringkasan Pengetahuan" = 13 kartu paragraf polos, terkesan kosong — konfirmasi keluhan owner. Masalahnya bukan panjang (avg hanya 114 char) tapi 100% teks: 0 list, 0 tabel, 0 gambar di dalam kartu | `#konten-produk .card = 13` (7 "Produk - Kulkas" + 6 "Produk - Lainnya"); panjang paragraf per kartu: avg **114,3** char, maks **161**, kartu >320 char = **0**; `ul/table` dalam main = 0/0 | Konversi isi jadi struktur: poin-poin jadi `<ul>`/chip/badge (contoh kartu "Rentang harga per segmen" → 4 baris segmen=harga), tambah angka menonjol (stat besar). Baseline struktur: 13 kartu 0 list 0 tabel → target tiap kartu punya minimal 1 elemen non-paragraf |
| P3 | Font terkecil di main = **11,2 px** pada badge kartu (`span.badge.inverter`), di bawah ambang keterbacaan umum 12 px | computed font-size terkecil 11,2 px (desktop & mobile sama); font sizes unik: 11,2 / 12 / 12,48 / … / 38,4 px | Naikkan badge ke >=12 px (12,48 px) saat rombak |
| — (sehat) | Katalog, filter chip, dan modal BERFUNGSI | 6 chip dengan hitungan benar (Semua 37 · Single Door 6 · Top Mount 15 · Bottom Mount 3 · Side by Side 5 · Multidoor 8); klik kartu → `.pk-modal.open` = true, tabel 8 baris, benefit 373 char, tutup via Escape = true | Tidak perlu diubah; jaga saat rombak (regresi) |
| — (sehat) | Nol error & nol h-scroll | console error = 0, pageerror = 0 di 2 viewport; h-scroll = false 1280 & 390; img broken = 0; img tanpa-alt = 0 | Pertahankan |

## proses.html

| Prioritas | Temuan | Bukti angka (hasil ukur) | Saran (baseline → target) |
|---|---|---|---|
| P1 | Kartu "Tahapan New Product Launch" = 8 langkah bernomor dijejalkan jadi SATU paragraf 356 char — konfirmasi keluhan owner "kartu paragraf panjang susun dibaca". Seluruh halaman tidak punya satu pun list/tabel | 8 kartu total; panjang paragraf avg **154,1** char, maks **356**; kartu >320 char = **1** (kartu launch, isi lengkap 8 langkah + PIC + tanggal di `proses.json` fakta[0]); `ul/ol` di main = **0**, `li` = **0**, `table` = **0** | Pecah kartu launch jadi checklist/timeline 8 baris (satu langkah = satu baris + badge status + PIC). **Baseline: 0 list elemen di main → target >=8 `<li>`.** Kartu "PIC per pekerjaan" juga cocok jadi tabel 2 kolom |
| P2 | 4 kartu soal latihan hanya memuat ketentuan/rule — data soal (14 baris per soal) dan kunci jawaban dari xlsx tidak dimuat sama sekali | `tugas.json` = 5 kartu; 0 tabel di main; angka jawaban (mis. total upah 9.484.200) tidak ada di halaman | Jadikan tiap soal accordion: soal (tabel data) + tombol "lihat kunci jawaban". Nilai kunci siap pakai — lihat section "Data materi belum kepakai" butir 6 |
| P3 | Font terkecil = **12,48 px** (label "Sumber:" `span.src`) — di batas bawah wajar | computed min font 12,48 px, konsisten 2 viewport | Opsional: 13 px saat rombak; bukan pemblokir |

Sehat: console error = 0, pageerror = 0, h-scroll = false (1280 & 390), img broken = 0, tanpa-alt = 0 (1 img = logo header).

## Data materi belum kepakai

Sumber = `tools\extracted\Rotation_-_REF__File_Rapih__Aqua_PM.xlsx.txt` kecuali disebut lain. Halaman produk saat ini hanya memakai rentang harga per SEGMEN (1 kartu), bukan per model.

1. **Harga e-commerce per model (33 baris AQUA, sheet 汇总)** — contoh: AQR-D185 Rp1.869.000 · AQR-D205 Rp2.031.107 · AQR-D225 Rp2.213.200 · AQR-DTM305RAV(MX) Rp4.570.000 · AQR-VTM535RSG(CL) Rp9.000.000 · AQR-CSE565RBC(CB) Rp8.659.000 · AQR-CSE605RBC(CB) Rp10.105.000 · AQR-CTD506RGG(BK) Rp9.479.000. Katalog live 0/37 punya harga → bisa jadi baris tabel modal + chip harga di kartu.
2. **Dimensi fisik per model (sheet 汇总 / sheet segmen)** — lebar x tinggi mm, contoh AQR-D185 525x1060 · AQR-DTM305RAV 545x1630 · SBS 830-905 x 1775. 0/37 di katalog; berguna buat halaman display plan.
3. **Sheet ANA — positioning & channel matrix**: per segmen ada "Compared With What Competitor", "Price Range (market)", Positioning (mis. 2 pintu inverter: "kapasitas akurat, hemat listrik, tahan lama, harga berkualitas dengan lapisan yang jelas"), matriks channel TRA/SM/B2B/ECOM/MM per segmen (1 pintu: TRA+SM only; lainnya full), dan insight "growth terbesar di 4-6 juta". Halaman hanya memuat 1 kartu ringkasan analisa — detail ini belum.
4. **Benchmark kompetitor ber-harga** (sheet Single Door / Top Mount (Inverter & Non-Inverter) / Side By Side / Multidoor): Sharp SJ-X198W-SB Rp2.599.000 · LG GN-B222SFIF Rp4.025.000 · Midea MDRS715FGF28ID Rp6.119.000 · Polytron PRA 18 MNX; plus Electrolux/Toshiba/Hisense/Hitachi. Nol tabel kompetitor di produk.html.
5. **HAIER 9 SKU + harga** (sheet HAIER): HRF-CTD579RAG(BK) 502 L Rp8.999.000 · HRF-CTD579RSG(BK)U1 Rp12.999.000 · HRF-CMD589RSG(WT)U1 512 L Rp20.999.999 dll. Katalog 37 model = 100% AQUA, 0 Haier — padahal logo situs Haier.
6. **Kunci jawaban + data lengkap 4 soal latihan** (`Tugas__Copy_of_Sharleen_Progress_100%_-_Latihan_Soal_Basic_for_MT.xlsx.txt`): total upah seluruh karyawan **9.484.200** · upah lembur >15 jam **4.137.250** · total komisi **6.319.950** · penjualan terbanyak **8.000.000** · biaya persalinan Bidan **1.650.000** · total biaya/hari kelas C **525.000**; tiap soal punya tabel data 9-14 baris. Bonus temuan: sheet "Soal 1"-"Soal 4" berisi jawaban SALAH (mis. pajak 2.025.000, seharusnya 13.500 — sheet "1"-"4" versi benar; sheet "Soal 3" menulis Bidan=100.000 melawan ketentuannya sendiri) → pakai angka sheet "1"-"4" sebagai kunci.
7. T588 (`Rotation_-_REF__T588-produk-baru-promosi.xlsx.txt`): SUDAH terpakai penuh di `proses.json` (semua 8 task + PIC + status masuk kartu launch). Tidak ada sisa berarti.

## Ringkasan 5 baris

1. produk.html sehat secara teknis (0 error, 0 h-scroll, modal klik+Escape jalan, 6 chip filter benar) — masalahnya konten visual: 37 kartu katalog 0 foto (JSON 0/37 field img, `produk.js` tak merender img) dan 13 kartu ringkasan 100% paragraf polos (0 list/tabel/img, avg 114 char).
2. proses.html juga 0 error & 0 h-scroll, tapi 8 kartunya paragraf polos semua (0 `<li>`, 0 tabel); terburuk kartu launch 356 char berisi 8 langkah → pecah jadi checklist/timeline.
3. Temuan: P1 = 2 (foto katalog; paragraf launch), P2 = 2 (kartu ringkasan tanpa struktur; soal tanpa data/kunci), P3 = 2 (font 11,2 px di produk; 12,48 px di proses).
4. Materi siap pakai yang belum masuk: harga per-model 33 AQUA, dimensi mm, positioning+matriks channel ANA, benchmark kompetitor ber-harga, 9 SKU Haier, kunci jawaban 6 angka + data 14 baris per soal (pakai sheet "1"-"4", bukan "Soal 1"-"4" yang salah hitung).
5. Baseline rombak: produk img 0→37, kartu ringkasan 0→13 elemen terstruktur; proses 0→>=8 `<li>`; jaga 0 error/0 h-scroll sebagai regresi pasca-rombak.
