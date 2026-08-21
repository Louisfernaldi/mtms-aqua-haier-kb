# Tiket 04 — Tampilkan perbandingan dan modal [BISA-DIBATALIN]
> Induk: `../../SPEC-fitur-perbandingan-dinamis-v1.md` · codex-fit: ya (UI vanilla dan E2E)

**Tujuan:** Tabel menampilkan kategori utama yang dipilih; modal menampilkan seluruh kategori per kelompok, bullet fitur, sumber per nilai, serta status kosong/saran secara jelas.
**Definisi selesai (cek mesin):** Playwright 1440px/390px melaporkan kategori utama cocok konfigurasi, kategori tambahan hanya di modal, console error 0, overflow halaman 0, dan tap target >=44px.
**Cara verifikasi:** fixture kategori banyak, nilai kosong, sumber ganda, saran bentrok, dan dua merek berbeda.
**File yang disentuh:** `site/kompetitor.html`, `site/js/product-detail.js`, `site/js/produk.js`, `site/css/style.css`, `tools/verify_product_detail.py`.
**Dependensi:** tiket 02 dan 03.
**Catatan tes:** wajib gerbang sabotase.
