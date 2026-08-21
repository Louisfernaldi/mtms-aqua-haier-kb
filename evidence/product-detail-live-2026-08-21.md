# Verifikasi Live Modal Detail Produk

deploy_ref: dl-20260821-1437-4116

- Waktu verifikasi: 2026-08-21 14:37 WIB
- URL: `https://master.mtms-aqua-haier-kb.pages.dev/`
- Commit: `4116d57fa06ae40bf462af6bc83771c54adcffcd`
- Cloudflare deployment: `97d2a12b`
- Rollback: deploy ulang worktree detached `D:\AI\tmp\win-temp\opencode\mtms-rollback-21bc57e`
- Verifier: `D:\AI\tmp\win-temp\opencode\verify_mtms_live.py`
- SHA-256 verifier: `AC163F399D90CA564E38E473D4DEF7BFEF3BA147BD1DF39FD681C95C43830C75`

## Versi Live

- SHA-256 `site/js/product-detail.js` lokal dan live: `b2cf90d1861dfff555d2c296b43117a1a9eb6b072accda26f629aad758586162`
- Login live: HTTP 200.
- Modal Kompetitor dan auto-open modal Produk diuji dari halaman live, bukan server lokal.

## Hasil Browser

| Viewport | Kompetitor | Produk | Foto | Scroll samping | Console error |
|---|---|---|---:|---|---:|
| 1440 x 900 | GC-L257CQEL | AQR-350RBM | naturalWidth 1600 | Tidak | 0 |
| 390 x 844 | GC-L257CQEL | AQR-350RBM | naturalWidth 1600 | Tidak | 0 |

Pemeriksaan tambahan lulus: modal bersama tampil, fitur hasil enrichment tampil, label `Sumber foto` jujur, gambar berasal dari `assets/kompetitor/`, tombol tutup minimal 44 x 44, Escape menutup modal, dan query `produk?model=AQR-350RBM` membuka record yang tepat.

## Screenshot Live

- Desktop: `evidence/product-detail-live-desktop.png`
- SHA-256 desktop: `5B5BF413AFDA5BD598902F9282754B032AE9CA85FC865B31A725313EDBA62B86`
- Mobile: `evidence/product-detail-live-mobile.png`
- SHA-256 mobile: `51891314112B89838565E8509C8A9509712B939E7624FF2F6D034FD076722835`

## Kontrol Negatif

Sebelum commit, ekspor `window.MTMSProductDetail` sengaja diputus. Verifier berubah merah dengan `AssertionError: Produk: singleton window.MTMSProductDetail.open belum tersedia`. Byte asli dikembalikan, lalu verifier kembali PASS.

## Vonis Mesin dan Juri

`LULUS`: versi live cocok dengan kandidat, dua viewport lulus, dan nol error browser.

- Juri pembukti: `ses_fdcbacae7ffeybae4taldy9ScM`
- Vonis: **LULUS**
- Alasan: pemeriksaan ulang live membuktikan deployment `97d2a12b` memuat JS commit `4116d57`; kedua ukuran layar membuka model yang tepat dengan gambar termuat, tanpa overflow, dan nol error console.
