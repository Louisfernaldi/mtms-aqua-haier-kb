# Tiket 02 — Bangun API dan editor dinamis [BISA-DIBATALIN]
> Induk: `../../SPEC-fitur-perbandingan-dinamis-v1.md` · codex-fit: ya (fungsi dan komponen teruji)

**Tujuan:** User login dapat menambah/edit/nonaktifkan kategori global, mengubah nilai per model, mengedit bullet, dan memilih kategori utama; edit user dikunci dari overwrite riset.
**Definisi selesai (cek mesin):** E2E lokal membuat kategori, mengisi AQUA+LG, reload, nilai tetap; fixture riset berbeda menghasilkan satu saran dan nilai user tidak berubah.
**Cara verifikasi:** Pages dev lokal + Playwright read/write ke fixture terisolasi, lalu restore otomatis.
**File yang disentuh:** `functions/api/produk.js`, `functions/api/kompetitor.js`, `functions/api/spec-categories.js`, `site/kompetitor.html`, `site/js/produk.js`, `site/js/product-detail.js`, `site/css/style.css`, `tools/verify_dynamic_specs.py`.
**Dependensi:** tiket 01.
**Catatan tes:** wajib gerbang sabotase.
