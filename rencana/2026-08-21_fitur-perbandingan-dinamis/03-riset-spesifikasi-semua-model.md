# Tiket 03 — Riset spesifikasi semua model [BISA-DIBATALIN]
> Induk: `../../SPEC-fitur-perbandingan-dinamis-v1.md` · codex-fit: tidak (riset web dan keputusan normalisasi)

**Tujuan:** Sensus 102 model, tetapkan 12 kategori inti dari data nyata, tarik spesifikasi resmi/cadangan sesuai hirarki, serta simpan provenance per nilai tanpa menulis live.
**Definisi selesai (cek mesin):** laporan menunjukkan denominator 102, tiap model punya status riset, setiap nilai non-user punya URL+timestamp, exact model match 100%, dan unresolved tercatat eksplisit.
**Cara verifikasi:** validator skema, sampel silang minimal dua model per merek, dan kontrol negatif model mirip.
**File yang disentuh:** `tools/research_specs.py`, `research/`, `evidence/spec-research/`, `site/data/spec-categories.json`, staging data hasil riset.
**Dependensi:** tiket 01.
