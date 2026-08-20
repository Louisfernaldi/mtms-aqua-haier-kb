# PAPAN ESTAFET — MTMS AQUA HAIER KB (audit total + penuntasan)

Sesi produktif 18 Agu 2026 · mandor: opencode sesi a91f3d · sumber: handoff `D:\.claude\handoffs\2026-08-18_mtms-audit-total-produktif_a91f3d.md`

Aturan gelombang (papan MENANG atas hitungan paralel): A → B → C → F → D → E → G
berantai PENUH (bukan paralel) karena irisan berkas `style.css`/`produk.html`/`data.js`
antar C-F-D-E. Tiket A sendiri = 3 subagen paralel dengan berkas temuan terpisah.

Deploy Cloudflare Pages tiap gelombang selesai + verify live + 1 baris deploy-log
(dilakukan MANDOR, ACC deploy situs ini sudah diberikan Louis di sesi ini).

| id | tiket | status | owner | verifier | depends_on | receipt |
|----|-------|--------|-------|----------|------------|---------|
| A | Audit total 7 halaman | kelar | subagen-audit-paralel | mandor-sesi-utama | - | evidence\A\receipt.md |
| B | Fix file:// embed data | kelar | codex-gpt-5.6-sol | mandor-sesi-utama | A | evidence\B\receipt.md |
| C | Foto produk katalog | belum-mulai | codex-gpt-5.6-sol | mandor-sesi-utama | B | evidence\C\receipt.md |
| F | Ringkasan Pengetahuan visual | belum-mulai | codex-gpt-5.6-sol | mandor-sesi-utama | C | evidence\F\receipt.md |
| D | AQUA vs Kompetitor + PDF | belum-mulai | codex-gpt-5.6-sol | mandor-sesi-utama | F | evidence\D\receipt.md |
| E | Rombak proses timeline | belum-mulai | codex-gpt-5.6-sol | mandor-sesi-utama | D | evidence\E\receipt.md |
| G | QC visual + laporan | belum-mulai | subagen-vision | mandor-sesi-utama | C,D,E,F | evidence\G\receipt.md |

## Gelombang 2 (H4-H8) — rombakan katalog 51 -> 45 kartu
Sesi produktif 18 Agu ~21:47-23:00 WIB · mandor: opencode sesi ini. Subagen: general x2 (H6+H7 rombak kartu, H5 riset spek). Semua tiket BERANTAI di produk-katalog.json.

| id | tiket | status | owner | verifier | receipt |
|----|-------|--------|-------|----------|---------|
| H4 | Pasang foto 14 model baru + berfile | selesai | mandor + gen_data_js | mandor | evidence\H4\receipt.md |
| H5 | Lengkapi spek (riset web) | selesai | subagen-general | mandor | evidence\H5\receipt.md |
| H6 | Pecah kartu gabungan RAP/RAV | selesai | subagen-general | mandor | evidence\H6\receipt.md |
| H7 | Gabung kartu dobel CBP | selesai | subagen-general | mandor | evidence\H7\receipt.md |
| H8 | QC visual final + laporan | selesai | mandor + vision free | mandor | evidence\H8\receipt.md |

## Posisi sekarang
- 18 Agu ~15:2x WIB: B kelar (34c2c960) + C kelar (ab3ac4a6, 27 foto+23 harga, jujur 27<30 krn sumber) + H kelar (0f81892d, fix 4 P1). Pekerja: opencode-go flash/pro (zen rate-limit, ACC Louis) + subagen sesi-utama. lanjut G (selesai).
- 18 Agu ~22:0x WIB (gelombang 2): H4-H8 selesai. Deploy master 4d121a0a (LIVE verified 45 kartu). Temuan luar lingkup: D185/D205/D225 dobel varian -> usulan gabung (nunggu Louis).

