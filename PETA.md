# Peta MTMS AQUA HAIER Knowledge Hub

- Situs: Cloudflare Pages `master.mtms-aqua-haier-kb.pages.dev`.
- Kode deploy: `site/`; Pages Functions: `functions/`; generator dan verifier: `tools/`.
- Data editable hidup: repo privat `Louisfernaldi/mtms-aqua-haier-kb-data`, dibaca lewat `/api/produk` dan `/api/kompetitor`.
- Data fallback deploy: `site/data/produk-katalog.json`, `site/data/kompetitor.json`, lalu di-embed ke `site/js/data.js`.
- Riset kompetitor lama: `D:\AI\projects\kompetitor-haier\komparasi-5brand\data\`.
- UI Produk: `site/produk.html` + `site/js/produk.js`.
- UI Kompetitor: `site/kompetitor.html`.
- Modal bersama: `site/js/product-detail.js`.
- SPEC aktif fitur dinamis: `SPEC-fitur-perbandingan-dinamis-v1.md`.
- Tiket: `rencana/2026-08-21_fitur-perbandingan-dinamis/`.
- SPEC gelombang galeri+insight: `SPEC-galeri-insight-engine-v1.md` · tiket+papan: `rencana/2026-08-21_galeri-insight-engine/` (brainstorm: `brainstorms/2026-08-21-galeri-insight-engine.md`).
- Hard-stop: deploy live dan tulisan data produksi butuh ACC; nol kirim customer, order, uang, atau harga marketplace.
