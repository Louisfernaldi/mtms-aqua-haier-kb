# Tiket 05 — Bangun tombol riset ulang [BISA-DIBATALIN]
> Induk: `../../SPEC-fitur-perbandingan-dinamis-v1.md` · codex-fit: tidak (job eksternal dan sumber web)

**Tujuan:** Tombol admin memulai riset satu model tanpa menahan halaman, menampilkan status, dan menaruh hasil sebagai saran yang dapat diterima/ditolak.
**Definisi selesai (cek mesin):** request start selesai <1 detik lokal, job idempoten per model, retry terbatas, user edit tidak berubah, dan hasil bentrok muncul sebagai saran.
**Cara verifikasi:** sumber cepat/lambat/404, klik ganda, model tidak dikenal, dan job parsial.
**File yang disentuh:** `functions/api/research.js`, `site/kompetitor.html`, `site/js/product-detail.js`, `site/css/style.css`, `tools/research_specs.py`, state job non-produksi.
**Dependensi:** tiket 02 dan 03.
