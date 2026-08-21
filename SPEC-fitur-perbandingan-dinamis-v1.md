# SPEC Fitur Perbandingan Dinamis v1

Status: RANCANGAN · 2026-08-21 WIB
Sumber: `D:\AI\state\brainstorms\2026-08-21-mtms-perbandingan-fitur-dinamis.md`
Keputusan produksi: `D:\AI\state\ronda\antrian-acc\KEPUTUSAN-mtms-aqua-haier-kb.md` bila deploy/tulis-live siap.

## Gambaran akhir
MTMS memiliki satu kamus kategori spesifikasi global yang berlaku untuk semua model AQUA, LG, Midea, Polytron, Samsung, dan Sharp. Tiap model tetap memiliki bullet `Fitur Unggulan`, ditambah nilai spesifikasi terstruktur yang bisa dibandingkan, diedit user, dan dilacak sumbernya. Riset web mengusulkan nilai baru lewat tombol `Riset ulang`, tetapi tidak pernah menimpa edit user otomatis.

## Masalah dan tujuan
- Modal saat ini memakai field tetap; data kosong walau tersedia di sumber pembanding.
- Fitur kompetitor belum cukup lengkap untuk perbandingan keputusan.
- User hanya bisa mengubah nilai tertentu dan belum bisa menambah kategori global.
- Halaman menunggu API sebelum merender sehingga terasa lambat.

Acceptance induk:
- Kategori baru dibuat sekali dan tersedia di seluruh model.
- User dapat memilih kategori utama yang tampil di tabel; kategori lain tetap ada di modal.
- Bullet fitur dan spesifikasi terstruktur sama-sama editable.
- Edit user menang; hasil riset berbeda menjadi saran dengan sumber, bukan overwrite.
- 102/102 model memiliki record valid; kekosongan disebut jujur, bukan ditebak.
- Initial render tidak menunggu API; editor hanya aktif setelah data live siap.

## Keputusan implementasi
- Skema global `spec_categories[]`: `key`, `label`, `group`, `unit`, `comparison`, `order`, `active`.
- Nilai per model `spec_values[key]`: `value`, `source_url`, `source_kind`, `verified_at`, `origin`, `user_locked`.
- `origin=user` atau `user_locked=true` tidak boleh ditimpa riset.
- Saran bentrok disimpan terpisah sebagai `research_suggestions[]` sampai user menerima/menolak.
- Hirarki sumber: situs merek -> toko resmi marketplace -> retailer besar -> sumber lain.
- Dua belas kategori inti ditetapkan setelah sensus sumber; detail resmi tambahan boleh melahirkan kategori non-utama.
- Tombol `Riset ulang` memulai pekerjaan terpisah dan langsung mengembalikan status; halaman tidak menunggu scrape selesai.
- Vanilla JS dan Pages Functions dipertahankan; nol framework/DB baru.

## Verifikasi
- Validator skema menolak key duplikat, kategori yatim, sumber invalid, dan overwrite user.
- Fixture bentrok membuktikan edit user tetap utuh dan saran riset tersimpan.
- E2E menguji tambah kategori global, isi nilai dua merek, pilih kategori utama, edit bullet, dan tampilan modal/tabel.
- E2E performa menunda API 4 detik tetapi tabel/kartu wajib muncul <1,2 detik lokal.
- Desktop 1440px dan mobile 390px: nol console error, nol overflow halaman, editor tetap dapat dipakai.

## Aturan kelas-1
- Tidak mengarang nilai. Setiap nilai riset punya URL sumber dan waktu cek.
- Perubahan user tidak pernah ditimpa diam-diam.
- Scrape dan deploy tidak satu transaksi; hasil scrape masuk staging/saran dulu.
- Tulis repo data live dan deploy Cloudflare Pages berhenti di ACC.
- Harga marketplace, order, customer, uang, dan n8n di luar cakupan.

## Sengaja tidak diubah
- Login bersama dan arsitektur Pages Functions.
- File materi/galeri/knowledge di luar Produk dan Kompetitor.
- Harga marketplace atau sistem transaksi apa pun.

## Risiko dan penjaga
- Istilah merek berbeda: normalisasi ke 12 inti, simpan label mentah sebagai provenance.
- Model mirip tertukar: pencocokan exact brand+model; kandidat fuzzy wajib review.
- Tabel terlalu padat: hanya kategori `comparison=true` tampil langsung.
- Edit saat data fallback: tombol edit disabled sampai API live selesai.
- Scrape lama/error: job status terpisah, retry terbatas, dan hasil parsial ditandai.
