# Progres MTMS AQUA HAIER

## Posisi sekarang
- 2026-08-22 (gelombang galeri-insight, 12/12 KELAR lokal — T11 integrasi-nav tuntas): T11 nav 12 link di 12/13 html (login 0 wajar) + 10 kartu index (6+4) + headless index/galeri 0 error 0 h-scroll @390/1280 + style.css tidak tersentuh; T12 deploy sebelumnya live (1c55076c) butuh RE-DEPLOY dengan ACC fresh untuk bawa T11. Papan: `rencana/2026-08-21_galeri-insight-engine/_ESTAFET.md`.
- 2026-08-21 (gelombang galeri-insight, 7/12 KELAR): T01 GFK JSON (47 brand, kontrol cocok) · T03 gate dibalik publik-kecuali-pasar/benchmark/strategi (statis lulus; runtime wrangler keblokir WinError32 = transport, bukti live ikut T12) · T04 galeri-v2.json 323 foto (OCR nunggu paket winrt, opsional) · T05 galeri museum UI (img=323, search, lightbox, mobile aman) · T06 file.html render tabel (headless 27 item nol error) · T07 benchmark 229 model + halaman · T10 update_semua.py 1-perintah (sabotase terbukti). SISA: T02 halaman pasar (siap), T08 strategi CEO (kerja Claude), T09 poster B2B, T11 nav (ANTRE sesi produk/kompetitor kelar), T12 deploy BUTUH-ACC. Papan: `rencana/2026-08-21_galeri-insight-engine/_ESTAFET.md`.
- 2026-08-21 (gelombang galeri-insight): grill 11 Q selesai (`brainstorms/2026-08-21-galeri-insight-engine.md`) → SPEC v1 + 12 tiket di `rencana/2026-08-21_galeri-insight-engine/`, gerbang estafet lulus (exit 0). Eksekusi G1 mulai: tiket 01/03/04/06/07. Tiket 11 antre sesi produk/kompetitor; tiket 12 BUTUH-ACC.
- 2026-08-21: modal detail Produk/Kompetitor live di commit `4116d57` dan terverifikasi.
- Hotfix lokal commit `1e37924`, belum deploy: AQUA mengisi kolom canonical yang kosong dari data Kompetitor, fitur duplikat disembunyikan, dan tabel/katalog merender fallback sebelum API selesai.
- Fitur perbandingan spesifikasi dinamis: discovery dan tiket 01 fondasi skema/migrasi selesai lokal; tiket 02-06 belum dimulai.

## Riwayat
- 2026-08-21: keputusan kategori global, user-edit-wins, kategori utama, 12 inti + temuan tambahan, tombol riset ulang, hirarki sumber, dan dua jenis data dicatat di brainstorm global.
- 2026-08-21: baseline live Kompetitor siap 1,1-3,5 detik dan Produk 1,8-2,2 detik; akar = render menunggu API GitHub.
- 2026-08-21: hotfix lulus verifier dengan API sengaja ditahan 4 detik tetapi render awal <1,2 detik; kontrol negatif tanpa render awal gagal pada 4,75 detik.
- 2026-08-21: 12 kategori inti dibekukan dari sensus 102 model + sampel resmi enam merek; migrasi sparse menghasilkan 102 record bermakna, kategori yatim 0, overwrite user 0, dan field lama hilang 0.
