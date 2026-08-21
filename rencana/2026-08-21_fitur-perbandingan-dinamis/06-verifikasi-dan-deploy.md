# Tiket 06 — Verifikasi dan deploy [BUTUH-ACC]
> Induk: `../../SPEC-fitur-perbandingan-dinamis-v1.md` · codex-fit: tidak (browser live dan deploy)

**Tujuan:** Jalankan seluruh gerbang offline, audit visual independen, siapkan rollback, lalu deploy satu kandidat ke Cloudflare Pages dan verifikasi live.
**Definisi selesai (cek mesin):** seluruh DOD exit 0; fingerprint live cocok commit; desktop/mobile console error 0 dan overflow 0; deploy-log serta bukti live tercatat.
**Cara verifikasi:** verifier lokal, negative control, classifier produksi, Playwright live, dan pembukti independen.
**File yang disentuh:** commit repo `Louisfernaldi/mtms-aqua-haier-kb`, Cloudflare Pages `mtms-aqua-haier-kb`, `evidence/`, `D:\AI\reference\deploy-log.md`.
**Dependensi:** tiket 04 dan 05.
**Gerbang:** commit/push boleh setelah audit; deploy live dan tulisan migrasi ke repo data produksi menunggu ACC Louis.
