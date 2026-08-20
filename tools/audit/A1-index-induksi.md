# Audit A1 — index.html & induksi.html (2026-08-18 13:00 WIB)

Target LIVE: `https://master.mtms-aqua-haier-kb.pages.dev/index.html` + `/induksi.html` (HTTP 200 keduanya).

## Metode
- Script headless: `D:\AI\tmp\win-temp\opencode\audit_a1.py` (Python + Playwright async, Chrome `"C:\Program Files\Google\Chrome\Application\chrome.exe"`), hasil mentah JSON: `D:\AI\tmp\win-temp\opencode\audit_a1_hasil.json`.
- Tiap halaman diukur di 2 viewport: **1280x800** (desktop) dan **390x844** (mobile), `wait_until="networkidle"` + tunggu 600 ms.
- Metrik: console error/pageerror, h-scroll (`scrollWidth > clientWidth+1`), img broken (`naturalWidth==0`) & tanpa alt, jumlah kartu (`.card/.pk-card/.stat/.tl-step/figure`) per section, paragraf padat (`p.textContent.length > 320` tanpa list/tabel/svg di host kartunya), section polos (tanpa `img/canvas/svg/table/iframe/video`).
- Verifikasi silang foto: HTTP HEAD langsung ke URL media live.
- Pembanding konten: `D:\AI\projects\mtms-aqua-haier-kb\tools\extracted\*.txt` (2 file >5 MB — `RAW_DATA_PC_MA...` 1,6 GB & `GFK_STDB...` 57 MB — hanya dibaca 50 baris pertama, tidak dibaca penuh).

## index.html

Dasar ukur: 6 img, 14 kartu total (6 `.kat-card` + 4 `.brand-fact` + 4 `.stat`), 15 heading, 14 `<p>`, **0 list, 0 tabel, 0 error** di kedua viewport.

| Prioritas | Temuan | Bukti angka (hasil ukur) | Saran |
|---|---|---|---|
| P2 | Img placeholder lightbox bawaan `src=""` + `alt=""` terhitung broken & tanpa-alt di hasil ukur | desktop: `img.broken=[""]`, `noAlt=[""]` (1 dari 6 img); elemen = `<img src="" alt="">` di overlay lightbox (index.html:155) | Beri `alt="pratinjau foto"` atau render img lightbox hanya saat dibuka (hidden + `src=""` terus kebaca alat ukur & screen reader) |
| P2 | 3 foto "Momen MTMS" `loading="lazy"` terukur `naturalWidth==0` di mobile (belum termuat saat ukur); file-nya HIDUP — bukan broken server | mobile-390: `broken` = 3 file (`media/27 Juli - Warehouse/IMG_8243.jpg`, `IMG_8244.jpg`, `media/SS Induction/IMG_8130.jpg`); HTTP HEAD live keduanya = **200 OK**; desktop: 0 broken | Foto pertama blok Momen MTMS kasih `loading="eager"` + `fetchpriority="high"` (efek LCP mobile); sisanya tetap lazy |
| P2 | Halaman 0 list / 0 tabel / 0 chart — semua konten kartu teks+emoji; 3 blok anak `main` polos tanpa visual | hasil ukur: `lists=0`, `tables=0`; `mainChildrenPlain`: `SECTION.hero` (294 chr), `DIV.grid` kartu topik (834 chr), `DIV.grid.brand-facts` (463 chr); section `.stats` (108 chr) & `.hero` juga polos | "Sekilas Brand" cocok jadi tabel kecil perbandingan (pangsa pasar 15,2% vs target) atau 1 mini-chart — data angkanya sudah ada di brand.json |
| P3 | Konsistensi angka statistik hero: "353 file" & "323 foto" muncul 2x (stats + footer + kartu galeri) | `section.stats`: 4 `.stat` (353/12/323/7); footer: "Dibuat dari 353 materi"; kartu galeri: "323 foto" — konsisten antar-lokasi, tapi tak ada sumber tautan ke `file.html` per angka | Ragu-ragu kecil: link-kan angka 353 → file.html & 323 → galeri.html biar bisa diverifikasi pembaca |
| P3 | Alt logo berulang sama ("Haier") di brand & showcase | 2 dari 6 img pakai `alt="Haier"` (logo nav + showcase) | Bedakan: `alt="Logo Haier — MTMS"` vs `alt="Logo Haier Group"` |

Ringkasan index: **P1=0 · P2=3 · P3=2**. Konsol & pageerror: 0 di kedua viewport. H-scroll: `diff=0` di 1280 maupun 390 (aman).

## induksi.html

Dasar ukur: konten dirender dari 5 JSON via `js/knowledge.js` → 28 kartu (Brand 7, Kulkas 5, Pemanas Air 6, TV 5, Cold Chain 5), 34 heading, 34 `<p>`, **0 list, 0 tabel, 0 img konten** (1 img = logo nav), 0 error di kedua viewport.

| Prioritas | Temuan | Bukti angka (hasil ukur) | Saran |
|---|---|---|---|
| **P1** | **Konten faktual SALAH di kartu "Sub-kategori kulkas"**: situs tulis `SB (side by side)` & `TD (2 pintu)` — sumber induksi Teh Lidia bilang **SB = Single Door, SE = Side by Side, TD = Four Door** | Live card (render dari `data/knowledge/induksi-kulkas.json` baris 18): "SE, TD (2 pintu), TM (2 pintu top mount), BM (bottom mount), **SB (side by side)**" vs sumber `SS_Induction__Kulkas+-+Teh+Lidia.docx.txt` baris 12: "SE-Side by Side, TD-Four Door, TM-Top Mount, BM-Bottom Mount, **SB-Single Door**" | Koreksi JSON: `SB (single door)`; `TD (four door)`; `SE (side by side)`. Ini materi belajar kode produk — salah arti = MT belajar keliru |
| P2 | 1 paragraf padat 336 karakter tanpa list di kartunya (teks dinding) | `denseP[0]`: len=336, "Kode produk punya 6 bagian: (1) brand: AQ=Aqua... (6) C/R = kompresor..." — padahal isinya persis daftar 6 butir; `lists=0` se-halaman | Pecah jadi `<ol>` 6 butir (atau render list dari JSON) — paling gampang diterapkan di knowledge.js saat `isi` berpola "(1)...(2)..." |
| P2 | Seluruh 5 section induksi polos: 0 img, 0 svg, 0 tabel, 0 chart di halaman | `plainSections` = 6/6 (hero-mini + 5 kb-sec, txtLen 119–1291 chr); `tables=0`, `svg=0`; sumber aslinya PUNYA tabel/materi visual (tabel spek SRP PDF Water Solutions hal.3; tabel perbandingan OS TV di TV PMT hal.6; diagram kode produk) | Tambah 1 visual per section: tabel SRP pemanas air, tabel perbandingan Smart/Android/Google TV, diagram anatomis kode `AQR-DTM285CBP` |
| P2 | Duplikasi isi kartu garansi antar section | `brand.json` fakta 7 "Garansi produk lain" (tangki 10/7 thn, elemen 2 thn) vs `induksi-water.json` fakta 6 "Garansi" (isi identik: tangki 10 thn/7 mekanikal, elemen 2 thn) — 28 kartu, 2 bawa info sama persis | Simpan rincian garansi di 1 tempat (induksi-water), kartu brand cukup sebut ringkasan + rujuk |
| P3 | Emoji kartu dari pencocokan kata pertama (`faktaEmoji`) bisa meleset | `knowledge.js:3-23`: match kata pertama; "Pemanas air: pengalaman global 40 tahun" match "air" → 💧 (pas), tapi kartu bertema garansi pemanas air match "garansi" → 🛡️ duluan — emoji bisa ganti-ganti tergantung urutan kata judul | Kecil — opsional: beri field `emoji` eksplisit di JSON biar stabil |

Ringkasan induksi: **P1=1 · P2=3 · P3=1**. Konsol & pageerror: 0. H-scroll: `diff=0` di kedua viewport. Semua 5 JSON ke-fetch sukses (28 kartu ter-render penuh, 2 viewport identik).

## Data materi belum kepakai (per file sumber, nilai konkret)

**1. `SS_Induction__Kulkas+-+Teh+Lidia.docx.txt`** (kartu situs baru pakai ~6 poin dari ~50)
- Baris 15: arti level lengkap — **S=Hero Model, A=Better, B=Good, Basic=Low End** (situs cuma nulis "Level produk: S, A, B, Basic" tanpa arti).
- Baris 44–46: instalasi standar — kulkas didiamkan **3 jam** sebelum dicolok (di PDF Ref Juli disebut metode "3,3,3": 3 jam diam–colok–isi).
- Baris 50: rak tempered glass tahan beban **50 kg**. Baris 53: Turbo Cooling Pro **-24°C**, es 1 jam. Baris 55: Chiller Box **-1°C**, daging/ikan segar 2–3 hari. Baris 56: Hygiene Deo Fresh hambat kuman **99,9%**.
- Baris 66: rumus biaya listrik **(Watt/1000) × jam × Rp 1.447/kWh** (tarif 900–2200 VA) — cocok jadi kalkulator mini.
- Baris 75–78: 4 tipe konsumen (pasif/ekspresif/teliti/agresif) + strategi approach — materi jualan yang belum ada sama sekali di situs.
- Baris 84: Big TM impor Vietnam **480 L, garansi 20 tahun, Smart IoT (High Smart)**. Baris 89: Haier **#1 kulkas dunia 18 tahun berturut-turut**. Baris 151–152: Nutribank (salmon 7 hari / daging 10 hari), Haier 650 L konsumsi **60 watt**. Baris 129–132: HCS jaga kelembaban 90%, buah-sayur utuh 2 minggu. Baris 112/128: water tank **4,5 L** & Magic Pitcher **1,6 L**.

**2. `SS_Induction__Water+Solution+-+Awan.docx.txt`** (kartu situs baru pakai ~7 poin)
- Baris 26–27: **harga** — non-WiFi 15 L ±Rp 1,5–1,6 jt, 30 L Rp 2,4 jt; WiFi 15 L Rp 3,2 jt, 30 L Rp 3,9 jt; **Rp 400 rb–1 jt lebih murah dari Ariston**.
- Baris 20: Shock Proof dipatenkan — tegangan turun ke **12 V** kalau bocor; ILCB di kabel. Baris 21: tangki besi bogang tahan **890°C**, PU foam 360° (turun 1°C/jam). Baris 16: suhu mandi eco **42–50°C**. Baris 14: 10 L=1 orang, 15 L=2 orang, 30 L=keluarga kecil.
- **Dispenser sama sekali belum punya kartu** di induksi (kategori situs hanya "Pemanas Air"): baris 33–48 — Quick Dispensing **3 detik/gelas** vs rata-rata 8–11 detik; tangki dingin **3,5 L** vs rata-rata 1–2 L; tinggi dispensing **25,5 cm**; harga elektrik Rp 1,6 jt / kompresor Rp 2,2–2,4 jt / UV Rp 2,8–3 jt; omzet toko >Rp 100 jt; rencana purifier 9 filter ±Rp 20 jt.

**3. `Product_Knowledge__Water_Solutions_-_2026_Juli.pdf.txt`**
- Baris 18–20 (tabel spek resmi): **SRP per model** — AES10V-SIM1 **Rp 1.365.600** · AES15V-SIM1 **Rp 1.737.000** · AES15V-SIW1 (WiFi) **Rp 2.853.000** · AES30V-SIM1 **Rp 2.137.200** · AES30V-SIW1 **Rp 3.501.600** (lebih presisi dari kisaran lisan di #2; kartu situs tidak menyebut harga sama sekali).
- Baris 69–78: proteksi 2 lapis — cut-off **75°C**, lalu thermostat mati otomatis di **95°C**. Baris 55–60: elemen enamel tahan korosi **30x**, anoda Mo **15x**. Baris 27: dimensi 350×350×265/335 mm (10/15 L) & 445×445×380 mm (30 L).

**4. `Product_Knowledge__Product_WS_Water_Dispenser_2026.pdf.txt`**
- Baris 8–28: model dispenser **AWD-617BE / AWD-605BC / AWD-1180BC** — panas ≥90°C (5 L/jam, 500 W); dingin ≤15°C @0,5 L/jam (BE, 65 W) vs ≤10°C @2 L/jam (BC, 85 W). Spek konkret utk kartu/tabel dispenser yang belum ada.

**5. `Product_Knowledge__Cold+Chain+-+Christie+(+AI+Refined).docx.txt`** (kartu situs pakai 4 dari ~30 poin)
- Baris 46: cooling retention **150 jam** saat listrik padam (PU foam). Baris 54: garansi kompetitor umumnya cuma 5 tahun vs Aqua **7+2**.
- Baris 71–73: deep freezer **-86°C** (cold brew, impor China), komersial **-60°C masuk Q4 2026**, rumahan high-end. Baris 76: **Ice Bar** masuk tahun depan.
- Baris 68: selisih harga antar toko bisa **Rp 500 rb–1 jt**. Baris 80–84: perawatan — jarak tembok **10–15 cm**, isi maksimal **70–85%**.

**6. `Product_Knowledge__CC_Product_For_Onboarding_2026.pdf.txt`**
- Hal. 2: **Indonesia NO.3 share 16,5% · SEA NO.1 15,2%** (situs hanya pakai 15,2% Asia — angka posisi Indonesia 16,5% belum dipakai).
- Hal. 7: **cara baca kode freezer `AQF-150DF`** (AQ=Aqua, F=Freezer, 150=kapasitas, DF=Deo Fresh) — pasangan alami kartu "baca kode kulkas", belum ada.
- Hal. 8: peta segmen High (DF/EC) — Mid (SD/HC/AB) — Low (MC "Market Champion"/BC/GO/GC/SBS/MB/CS). Hal. 19: Air Freeze Inverter — pembekuan **14 kg/24 jam**, retention **126 jam**, -26~10°C.

**7. `Product_Knowledge__TV+-+ANDIKA.docx.txt`** (kartu situs pakai 4 dari ~25 poin)
- Baris 18: OLED seri C95 65" **Rp 28–30 jt**. Baris 24: Mini LED 85" **Rp 24 jtan**. Baris 20/25–26: speaker **Harman Kardon** (OLED) / **KEF** (Mini LED). Baris 30–32: QLED **1000 level gradasi warna**, seri terlaris **S80 (43–65")**, Q80 2026 bawa AI. Baris 38: TV terbesar **100"** Mini LED + AI PQ. Baris 41/54: Google TV **>5.000 aplikasi** vs Tizen ±1.600. Baris 50: Hisense/Toshiba pindah ke Vida. Baris 39: 32"=FHD, 43"+=4K.

**8. `Product_Knowledge__Aqua_TV_one-pager.pdf.txt`**
- C95 65": **144 Hz, RAM/ROM 3G+32G, Dolby Vision+Atmos, VRR/ALLM** (hal. 2). S90F 100": **240 Hz gaming, 432 dimming zones, 4G+64G** (hal. 5). M80: dimming zones per ukuran **360(85")/286(75")/220(65")/160(55")** (hal. 4). S80 43–65": 120 Hz DLG. Q80G lineup penuh 32F–85" (hal. 8). Semua angka spek jadi tabel lineup TV yang belum ada di induksi-tv.

**9. `Product_Knowledge__TV_Product_Knowledge_-_New_PMT.pdf.txt`**
- Hal. 8: **cara baca kode TV `AQT65Q80GUX`** (AQT=AQUA TV · 65=inch · Q80=seri · G=2026 · U=UHD 4K · X=Google TV; E=2024/F=2025/G=2026, F=FHD, -=HD) — kartu "baca kode TV" belum ada, padahal induksi kulkas sudah punya padanannya.
- Hal. 6: tabel perbandingan Smart TV vs Android TV vs Google TV (Play Store, Google Assistant, Chromecast built-in, harga) — siap jadi tabel HTML.
- Hal. 8: peta lineup 2026: OLED C95 → QD-MiniLED M96/M92 → MiniLED M80/N85 → QLED S800–S80 → Basic LED A85–A75.

**10. `Rotation_-_REF__File_Rapih__Ref_-_2026_Juli.pdf.txt`**
- Hal. 5: metode instalasi **3,3,3** (3 jam diam / 3 jam colok kosong / 3 jam isi bertahap) — versi lebih lengkap dari "diamkan 3 jam".
- Hal. 7–23: **daya listrik per SKU** (contoh: AQR-D185 145 L 67 W; AQR-DTM285RAP 225 L 33,8 W; AQR-VTM535RSG 480 L 56 W; SBS CSE696RSV 618 L 42 W; TTD746 658 L 40 W) — kandidat tabel "kapasitas vs watt" yang belum ada di induksi/produk.
- Hal. 6: Giant Freezer kapasitas 13% lebih besar; HCS kelembaban 90%. Hal. 4: layanan pelanggan **0800 1 003 003** (SMS & WhatsApp) — belum muncul di mana pun di 2 halaman audit.

**11. File raksasa (dibaca 50 baris pertama saja, sesuai amanat)**
- `Rotation_-_REF__File_Rapih__RAW_DATA_PC_MA_LY2025_&_FY2026_(MTD_1-10_August_'26).xlsb.txt` (1,6 GB): baris transaksi penjualan per-SKU PC MA (toko, region, model, qty, nilai Rp — contoh r14: AQT55P750UX TV 55" Rp 6.099.000, Bali). Relevan untuk **rotasi.html**, bukan index/induksi; potensi "harga jual nyata per model" kalau diagregasi.
- `Rotation_-_REF__GFK_STDB_COOLING_ID_HAIERASIAINTERNATI_Jun25.xlsx.txt` (57 MB): sheet "Market Share" — **Aqua unit share 14,67% & value share 12,25%** (JABOTABEK, periode 2026-06-25), tabel per-region 7 wilayah & per-brand (Sharp 32,3% unit, Polytron 27,0%). Angka market share konkret buat halaman rotasi; index/induksi tidak butuh.

## Ringkasan 5 baris
1. Kedua halaman **0 console error, 0 pageerror, 0 h-scroll** di 1280x800 & 390x844; semua JSON induksi ke-fetch sukses (28 kartu ter-render penuh).
2. **1 temuan P1**: kartu "Sub-kategori kulkas" live menulis SB=side by side & TD=2 pintu — sumber Teh Lidia (baris 12) jelas SB=Single Door, SE=Side by Side, TD=Four Door; salah kaprah materi belajar, tinggal koreksi 1 baris JSON.
3. Kelemahan struktur utama: **0 list / 0 tabel / 0 chart** di kedua halaman (diluar 0 visual di induksi) — padahal sumber punya tabel SRP pemanas air (Rp 1,37–3,5 jt), tabel OS TV, dan tabel daya-per-SKU siap pakai.
4. Banyak data angka bernilai belum dipakai: harga & SRP pemanas air/dispenser, kode TV `AQT65Q80GUX` & kode freezer `AQF-150DF`, cooling retention 150 jam, posisi Indonesia NO.3 16,5%, garansi vs kompetitor — total 10 file sumber dengan nilai konkret di atas.
5. Foto "Momen MTMS" live sehat (HTTP 200) tapi lazy-terukur-0 di mobile — naikkan prioritas foto pertama; img lightbox `src=""` perlu alt supaya bersih di alat ukur & screen reader.
