# Audit A3 — rotasi/galeri/file (18 Agu 2026 13:10 WIB)

## Metode
- Target LIVE `https://master.mtms-aqua-haier-kb.pages.dev/{rotasi,galeri,file}.html`, headless Python Playwright async, Chrome `C:\Program Files\Google\Chrome\Application\chrome.exe`, viewport 1280x800 (desktop) & 390x844 (mobile), wait networkidle + 600 ms (galeri: networkidle timeout 60 s → fallback domcontentloaded + 4 s, lalu scroll-ke-bawah berulang maks 60x seperti lazy-load user).
- Pengukuran via `page.evaluate` DOM: console/pageerror, h-scroll (`scrollWidth - clientWidth`), img broken (`complete && naturalWidth===0`) & tanpa-alt, section polos (0 img/canvas/svg/table), font terkecil + rasio kontras (WCAG luminance).
- Link file: cek `href` kosong via DOM + panjang byte live via ranged-GET `Range: bytes=0-0` (baca `Content-Range`; Cloudflare Pages tidak selalu mengirim Content-Length di HEAD).
- Cross-check sumber lokal `site\` (galeri.json 323 entri vs 323 file fisik; files.json 28 entri vs 28 file fisik) + materi `tools\extracted\Rotation_-_REF__*.xlsx.txt`.
- Script: `D:\AI\tmp\win-temp\opencode\audit_a3.py`, `audit_a3b.py` (read-only terhadap site\; tidak ada berkas di site\ yang diubah).

## rotasi.html

| P | Temuan | Bukti angka (ukur) | Saran |
|---|--------|--------------------|-------|
| P1 | **Semua 4 chart DOBEL-RENDER** — tiap host berisi 2 SVG identik menumpuk (akar: `charts.js:102` `chartsInit()` di DOMContentLoaded **plus** inline script `rotasi.html:86-106` memanggil `draw*` lagi ke host yang sama). Label/nilai jadi ganda dempet. | `svgCount=2` di 4/4 chart; `chart-share-unit` rects **18** (9 bar × 2), texts 55; `chart-peta-harga` circles **16** (8 titik × 2). 0 console error — defect senyap. | Hapus salah satu jalur: buang panggilan inline di rotasi.html ATAU buang `chartsInit`+listener dari charts.js. |
| P2 | Teks chart nyaris tak terbaca di HP — host 324 px memuat SVG viewBox 760 px (skala 0,43), label 11 px → **≈4,7 px efektif**, subLabel 9 px → ≈3,8 px. | Desktop hostWidth 1022 / mobile **324**; **134 elemen teks <12 px**; font terkecil terukur 9 px (kontras aman 13,81:1). | Redraw chart per-viewport (W mengikuti host) atau tabel fallback di mobile; naikkan font svg min 12. |
| P2 | 0 `<canvas>` — semua chart SVG (metrik "canvas width>0" = 0, tapi 4 host keisi). Bukan bug, catat supaya metric dibaca benar. | canvasCount 0; 4 host chart keisi SVG. | — |
| P3 | 1 paragraf >320 karakter (kartu "Peta harga-kapasitas Haier", 328 kar — deretan harga 8 model). | bigPCount 1, len 328. | Pecah jadi list per model. |
| P3 | 4 section tanpa visual (`hero-mini` + 3 `kb-sec` kartu teks) — by design, bukan kosong cacat. | plainSec = 4. | — |

Sehat: h-scroll 0 (desktop & mobile), console error 0, pageerror 0, img broken 0, tanpa-alt 0. Konten: **16 kartu fakta** (5 pasar + 6 benchmark + 5 dealer) dalam 3 kb-sec — sesuai 3 JSON.

## galeri.html

| P | Temuan | Bukti angka (ukur) | Saran |
|---|--------|--------------------|-------|
| P1 | **Foto hampir tak termuat saat diguling** — pengunjung yang scroll langsung ke bawah lihat mayoritas placeholder. Setelah scroll-ke-bawah berulang sampai halaman mentok: desktop **22/323 termuat** (301 pending), mobile **1/323** (322 pending). Foto di atas tak pernah di-load ulang. (Pengukuran scroll-instan headless memang ekstrem, tapi arahnya jelas: fetch ±1,3 MB/foto kalah cepat oleh scroll.) | post-scan: fig 323, img 323, loaded 22 (desktop) / 1 (mobile); `performance` imgResources 23 (8 MB) desktop, 2 (mobile). 0 broken, 0 console error. | Kecilkan foto (resize + WebP, target <150 KB/thumbnail) atau tambah width/height + decoding hint; sisipkan skeleton agar terasa jalan. |
| P1 | Halaman tak pernah "diam": `networkidle` **timeout 60 s** di desktop & mobile — cascade render group (IntersectionObserver 600 px, `galeri.html:108-116`) + fetch foto besar membuat jaringan terus sibuk. | goto timeout 2/2 viewport; setelah fallback, 7 group tetap kebentuk penuh (fig 323). | Sama di atas (payload kecil = networkidle tercapai). |
| P2 | **Total media 429,4 MB / 323 foto, rata-rata 1,33 MB per foto** — foto kamera asli dipakai apa adanya, tanpa thumbnail. Di jaringan HP ini beban besar utk grid kecil. | os.walk `site\media`: 323 file, 429,4 MB; 0 file 0-byte. | Optimasi gambar batch (tiap foto ≤200 KB versi web). |
| P2 | Lightbox **jalan**: klik figure pertama → `div.lightbox` dapat class `open`, `img src` terisi, caption terisi; tombol prev/next/close terpasang (`lightbox.js:29-47`). | lightbox {open:true, filled:true, src=…IMG_8240 2.jpg, cap:"IMG_8240 2"} di 2/2 viewport. | — |
| P3 | Klaim "323 foto" **tepat**: 323 entri galeri.json = 323 file fisik (321 match persis + 2 nama ber-`%20` yang sama file), 7 group semua ke-render. | figTotal 323; groups 7; matched 323. | — |

Sehat: h-scroll 0, broken 0, tanpa-alt 0, console error 0, pageerror 0, section polos hanya hero-mini.

## file.html

| P | Temuan | Bukti angka (ukur) | Saran |
|---|--------|--------------------|-------|
| P1 | **Link PDF 0-byte hidup di LIVE** — "Sharleen - Warehouse Visit Report- Management Trainee 2026.pdf" bisa diklik, status 200, tapi isinya kosong: unduhan = PDF 0 KB. File fisik lokal juga 0 byte (`site\files\Tugas\...pdf`), label ukuran "0 B" tampil di halaman. | ranged-GET live `Content-Range: bytes 0-0/0` (total 0); os.path.getsize lokal = 0. | Ganti file sumber (minta ulang PDF-nya) atau sembunyikan entri sampai file ada. |
| P2 | **Kalimat hero menyesatkan**: "File besar (>25 MB) tersedia lewat link Drive" — **0 link [Drive]** di seluruh halaman; file terbesar yang dipajang 18,4 MB (CC Catalog.pdf), tidak ada satu pun >25 MB. | driveCount 0/28 link; ukuran max di files.json = 18,4 MB. | Hapus kalimatnya, atau tambahkan link Drive bila file raksasa (RAW DATA 1,6 GB) memang mau dibagikan. |
| P2 | **Klaim 29 file vs aktual 28** — brief bilang "files.json (29 file)"; terukur 28 li / 28 link / 28 entri JSON / 28 file fisik. Halaman konsisten dengan datanya; angka 29 di brief yang salah. | liCount 28, linkCount 28, 5 group; os.walk files = 28 (60,2 MB). | Koreksi angka di brief/registry. |
| P3 | Semua link hidup: 0 `href` kosong; ranged-GET 28/28 status 200 (Cloudflare tidak kirim Content-Length di HEAD, makanya dipakai ranged-GET). | emptyHref 0; status 200 × 28. | — |

Sehat: h-scroll 0, console error 0, pageerror 0, img broken 0, font terkecil 13,6 px kontras 13,81:1.

## Data materi belum kepakai
(angka benchmark kompetitor bagus yang BELUM muncul di rotasi.html — sumber file tercantum)

1. **Harga NET kompetitor SBS dari EC BENCHMARK (Jul 26)** — chart `chart-sbs-ec` cuma 4 bar AQUA; 12 model kompetitor ada di materi, 0 dipakai: Samsung RS70F65KNFSE/BL 660L **Rp17.799.000** & RS70F65QNFSE/BL 680L Rp14.399.000 & RS57DG4000M9/SL 570L Rp9.369.000; Electrolux ESE6645A 600L Rp14.609.000, ESE6600B-B 624L Rp13.149.000, ESE5100-B 545L Rp11.559.000, ESE4500A-B 450L Rp8.979.000; Toshiba GR-RS696WE 620L Rp8.799.000, GR-RS600WI 460L Rp8.629.000; LG GCFB507PQAM 509L Rp9.499.000; Midea MDRS715FGF28ID 558L Rp6.999.000; Modena P650SBS 546L Rp8.259.000; Hisense RS708N4IBU 591L Rp8.599.000; TCL PRS 520Y 550L Rp6.799.000. → `Rotation_-_REF__File_Rapih__EC_BENCHMARK.xlsx.txt` baris 5-8.
2. **Multidoor & TM kompetitor (EC)**: Sharp SJ-IF91PG-GB 639L Rp17.279.000; Hisense RQ630N4IGUI3/GY 664L Rp12.999.000; Toshiba RQ561N4IWU 507L Rp11.779.000; Midea MDRF550FGF28ID 407L Rp7.999.000; Polytron PRS 510X 436L Rp10.519.000. TM: Samsung RT25FARBDB1 Rp6.539.000; Sharp SJ-326XI-MK Rp5.119.000; LG GN-B212PQNF Rp4.935.666; Polytron PRW 23MNX Rp3.849.000. → EC_BENCHMARK baris 9-21.
3. **3 insight keputusan manajemen dari Benchmark_Kulkas_Indonesia_Agu2026** (sheet 2_Ringkasan baris 63-65) — belum ada di halaman mana pun: (a) Haier 779RAA ±Rp25,7 rb/L LEBIH MURAH per liter dari flagship Sharp ±Rp29,1 rb/L (more-for-the-same, bukan premium); (b) lubang portofolio Rp22-35 jt (Samsung sendirian); (c) entry 502L Rp8,99 jt berisiko kanibalisasi AQUA. Plus matriks segmen: Haier **0 SKU SBS** vs LG 3; Sharp 6 SKU 2-pintu. → `..._Benchmark_Kulkas_Indonesia_Agu2026.xlsx.txt` baris 63-65, 156-161.
4. **Rentang harga pasar per segmen (Aqua PM sheet ANA)**: 1 pintu 2-3 jt ("paling kompetitif 2-2,5 jt, margin tipis"); 2 pintu inverter 3-6 jt ("Aqua value / LG premium / Sharp economist"); SBS 8-11 jt (range AQUA terluas kedua setelah Electrolux 8,65-15,0 jt, separuh lineup numpuk 8,6-9,2 jt); MD 10-12 jt. Plus harga e-commerce konkret 1 pintu: AQR-D185 Rp1.869.000 vs Sharp SJ-X198W Rp2.599.000 vs Polytron PRA18 MNX Rp2.475.000. → `..._Aqua_PM.xlsx.txt` baris 9-13, 18-20.
5. **Bandingin Produk.xlsx** — 90% sel kosong (nama model tanpa kapasitas/harga); nilai ekstraksi rendah, cukup dipakai sebagai daftar model (sudah terwakili di kartu "Perbandingan 1 pintu"). → `..._Bandingin_Produk.xlsx.txt`.

**Baseline section pembanding 6 brand (LG/MIDEA/POLYTRON/SAMSUNG/SHARP) = BELUM ADA, terkonfirmasi angka:** 0 chart dan 0 tabel harga-spesifikasi kompetitor di ketiga halaman. Yang ada cuma: (a) bar pangsa pasar GFK (`rotasi.html:87-91` — angka share, bukan benchmark produk), (b) satu kalimat penyebut nama brand tanpa angka (`rotasi.html:60`), (c) kartu teks JSON menyebut beberapa model kompetitor berharga (rotasi-dealer.json: LG GCFB41FPGAM Rp10.235.015; Sharp SJ-IF51PG Rp10.199.000). Audit ini = baseline "belum ada" yang sah untuk section baru di produk.html.

## Ringkasan 5 baris
1. rotasi.html: 4/4 chart DOBEL-RENDER (svgCount 2, rects 18 utk 9 bar) — akar charts.js `chartsInit` + inline script bentrok; teks chart mobile efektif <5 px.
2. galeri.html: struktur sehat (323/323 foto, 0 broken, lightbox jalan) tapi pengalaman berat — 429 MB total foto, mobile hanya 1/323 termuat saat scroll, networkidle tak pernah tercapai (timeout 60 s).
3. file.html: 1 PDF 0-byte hidup live (unduhan kosong), kalimat "link Drive" tanpa satu pun link Drive (0/28), klaim 29 file vs aktual 28.
4. Materi kompetitor kaya tapi 0 terpakai di chart: 12+ harga NET SBS/multidoor/TM 6 brand + 3 insight keputusan (kanibalisasi 502L, lubang Rp22-35 jt, more-for-the-same) siap jadi section baru.
5. Semua klaim di atas angka hasil ukur headless 18 Agu 2026 13:10 WIB; script + JSON mentah: `D:\AI\tmp\win-temp\opencode\audit_a3*.py` / `audit_a3_result*.json`.
