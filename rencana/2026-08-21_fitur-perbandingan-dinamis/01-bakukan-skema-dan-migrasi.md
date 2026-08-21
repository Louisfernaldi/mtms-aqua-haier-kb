# Tiket 01 — Bakukan skema dan migrasi [BISA-DIBATALIN]
> Induk: `../../SPEC-fitur-perbandingan-dinamis-v1.md` · codex-fit: ya (schema, migrator, validator)

**Tujuan:** Tambahkan kamus kategori global, nilai terstruktur per model, saran riset, serta migrator idempoten dari JSON lama tanpa kehilangan field.
**Definisi selesai (cek mesin):** `python -X utf8 tools/verify_dynamic_specs.py` melaporkan 102/102 model valid, kategori yatim 0, key duplikat 0, dan migrasi dua kali menghasilkan hash sama.
**Cara verifikasi:** fixture data lama, data kosong, key duplikat, sumber invalid, dan nilai user-locked.
**File yang disentuh:** `tools/migrate_dynamic_specs.py`, `tools/verify_dynamic_specs.py`, `site/data/spec-categories.json`, `site/data/kompetitor.json`, `site/data/produk-katalog.json`, `tools/gen_data_js.py`.
**Dependensi:** nol.
**Catatan tes:** wajib gerbang sabotase.

**Sumber keputusan kategori:** `../../evidence/taxonomy-research-2026-08-21.md`.
