# Tiket H4-H8 — Rombakan Katalog Produk (foto + spek + kartu)

`estafet
id: H4-H8
status: selesai
depends_on: [H2, H3]
owner: subagen-general + mandor-sesi-utama
`

| id | tiket | status | bukti |
|----|-------|--------|-------|
| H4 | Pasang foto 14 model baru + model lama berfile | selesai | 38/45 kartu berfoto_list, 0 prefix salah, modal 4 thumbs, 0 err; 7 tanpa foto = file tak ada |
| H5 | Lengkapi spek 14 model baru | selesai | varian/flags/serie CTD506RGC/GG, material+garansi+varian+flags 405IG/355IG/355IM, nett CBP 245/265/285; daya 7 model tetap null (spek gambar-only) |
| H6 | Pecah kartu gabungan RAP/RAV | selesai | 3 kartu "/" dihapus -> 6 kartu individual lengkap harga RAP vs RAV; nol label "/" |
| H7 | Gabung kartu dobel CBP tanpa foto | selesai | DTM248/268/288CBP 2->1 kartu (varian 7, serie gabung) |
| H8 | QC visual final + laporan | selesai | evidence\H8\qc-visual.md |

- Rombakan: 51 kartu -> 45 kartu (42 model unik; D185/D205/D225 dobel = temuan luar lingkup).
- Deploy: ea32acfa (production main, 15:03 WIB) + 4d121a0a (branch master = alias live, 22:0x WIB). Deploy-log 1 baris.
- Catatan: mtms_deploy.py tidak menaruh `--branch`, jadi deploy masuk production main; URL live resmi = alias master -> deploy ulang pakai --branch master. Usulan fix mtms_deploy.py di LAPORAN.
- Backup: evidence\H6\produk-katalog.before.json (sebelum H6+H7), evidence\H5\produk-katalog.before-h5.json (sebelum spek).
