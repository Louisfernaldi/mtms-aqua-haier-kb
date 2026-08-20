# Receipt Kerja — H6: Pecah RAP/RAV + Gabung CBP

Tanggal: 18 Agu 2026 · Pelaksana: pekerja rombak data (verifikasi mandiri, lapor jujur)

## Apa yang diubah
1. **3 kartu gabungan RAP/RAV dihapus** (data lengkapnya dipindah ke kartu individual).
2. **6 kartu draft placeholder RAP/RAV diperbaiki** (isi dari kartu gabungan + riset AQUA):
   kapasitas, daya, material, garansi, varian per varian (FB/MX), flags Inverter, benefit verbatim
   dari kartu gabungan, harga + harga_source="official-page" dari `komparasi-5brand\data\riset_brand\AQUA.json`.
   Field `foto` TIDAK diisi (absent, generator yang mengisi). Field `fitur` draft lama dihapus
   (pola kartu gabungan tidak memakainya).
3. **3 pasang kartu dobel CBP digabung jadi 1 kartu per model**:
   varian gabung 7 item, serie "Chic Color / Magic Neo", benefit digabung dari 2 teks yang ada
   ("...Chic Color Series & Magic Neo Series, non-inverter..."), kapasitas/daya/material/garansi/flags
   ikut data yang sudah ada (kedua kartu identik, divalidasi mesin sebelum digabung).
   Harga tetap tanpa field (tidak ada sumber — pola lama file).

## Jumlah kartu
- Sebelum: **51** (diverifikasi script, assert `len==51`)
- Sesudah: **45** (diverifikasi script, assert `len==45`)

## Kartu dihapus (3)
- AQR-DTM265RAP/RAV (gabungan)
- AQR-DTM285RAP/RAV (gabungan)
- AQR-DTM305RAP/RAV (gabungan)

## Kartu digabung (6 → 3)
- AQR-DTM248CBP (Chic Color + Magic Neo → 1 kartu)
- AQR-DTM268CBP (Chic Color + Magic Neo → 1 kartu)
- AQR-DTM288CBP (Chic Color + Magic Neo → 1 kartu)

## Kartu diperbaiki (6)
AQR-DTM265RAP, AQR-DTM265RAV, AQR-DTM285RAP, AQR-DTM285RAV, AQR-DTM305RAP, AQR-DTM305RAV
(harga 3860000/3975000/4034000/4155000/4736000/4878000 — cocok dengan AQUA.json price_idr)

## Hasil verifikasi (LANGKAH 3)
- Jumlah kartu final: **45** ✓
- Model mengandung "/": **0** ✓
- Model unik: **42** — 3 nama model punya 2 kartu (AQR-D185, AQR-D205, AQR-D225, pasangan
  Chic Color/Magic Neo) yang SUDAH ADA sebelum pekerjaan ini; di luar lingkup H6 (instruksi cuma
  menyebut CBP 248/268/288), jadi TIDAK digabung — dilaporkan jujur, bukan "diperbaiki" mengarang.
- Harga 6 kartu RAP/RAV: semua benar (6/6) + varian FB/MX benar ✓
- CBP 248/268/288: masing-masing 1 kartu, varian 7 item, serie "Chic Color / Magic Neo" ✓
- Struktur: 45/45 kartu punya 14 key dasar (model, brand, group, kategori, range,
  kapasitas_gross, kapasitas_nett, daya_watt, material, garansi_tahun, varian, flags, serie, benefit) ✓
- Kartu tak tersentuh: 36 identik byte-level vs backup (Counter JSON == ) ✓
- JSON valid: `json.load` exit 0 ✓
- verify_file_proto.py: `=== 51` → `=== 45` (hanya 1 baris itu)

## Hash
- Backup (`evidence\H6\produk-katalog.before.json`):
  `376b0bf58068a4bb9cd97bfb20d772309779ae57c6eb0fcd2c2c19dcf764c79b`
- Final (`site\data\produk-katalog.json`):
  `5586635660d60630f2fbc3582700ac0a2d1f315834b14234adbfb2f9684435a9`

## Catatan
- Tool bantu transformasi = skrip temp di `D:\AI\tmp\win-temp\opencode\pecah_gabung_h6.py` (di luar project).
- Draft AQR-DTM245CBP / 265CBP / 285CBP (tanpa varian, tanpa harga) TIDAK disentuh — bukan bagian lingkup.
