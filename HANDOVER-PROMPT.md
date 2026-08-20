# PROMPT HANDOVER — Optimasi Website MTMS AQUA HAIER Knowledge Hub
> Louis forward blok di bawah ini ke sesi lain yang lagi ngerjain gambar produk. Sesi ini (yang bikin prompt) SUDAH selesai: situs live, materi terkumpul, data pengetahuan terstruktur. Yang tersisa = SEMUA di bawah.

---

TUGAS LANJUTAN (Louis, 17 Agu 2026 malam): optimasi website **MTMS AQUA HAIER Knowledge Hub** — https://mtms-aqua-haier-kb.pages.dev (Cloudflare Pages, project `mtms-aqua-haier-kb`, token `D:\Secret\cloudflare-pages-token.txt`).

## Konteks yang SUDAH ADA (jangan dibangun ulang)
- Folder proyek: `D:\AI\projects\mtms-aqua-haier-kb\` — `site\` (situs), `materi-drive\` (353 materi asli dari Google Drive Sharleen), `tools\extracted\` (29 teks hasil ekstraksi PDF/DOCX/XLSX/XLSB), `site\data\knowledge\*.json` (12 file fakta terstruktur dari materi asli).
- Situs 7 halaman (index/induksi/produk/rotasi/proses/galeri/file), 323 foto di `site\media\`, 29 file asli di `site\files\`, pencarian + dark mode + 4 chart SVG sudah jalan.
- Environment: Python 3.14 + pdfplumber/python-docx/openpyxl/pyxisbs/playwright; Chrome `C:\Program Files\Google\Chrome\Application\chrome.exe`; wrangler terpasang; verifikasi headless = 0 console error + 0 h-scroll ≤390px (pola: `tools\verify_site.py`).

## TUGAS (urut prioritas)
1. **GAMBAR PRODUK (punya kamu!)** — kamu sedang bikin gambar produk. Pasang hasilnya ke situs: slot `site\media\produk\` + referensi JSON di `site\data\` — halaman produk cukup baca folder itu, jadi nol ubah HTML per gambar. Foto yang ada sekarang (24 foto produk AC-SS di `site\media\Product Knowledge\AC - SS\`) dipakai dulu sebagai isi sementara.
2. **PRODUK KLIK-ABLE + DETAIL**: di halaman Produk, tiap produk jadi KARTU yang bisa diklik → HALAMAN DETAIL (foto besar, spesifikasi, garansi, harga, sumber materi). Kategori pertama: KULKAS (data kompetitor terlengkap). Sumber data: `tools\extracted\` (EC BENCHMARK, Bandingin Produk, AQUA REF Product Mapping, POP Listrik, Benchmark Kulkas Agu2026, Diagram Sebar, Product_Benchmark).
3. **PERBANDINGAN KOMPETITOR**: di halaman detail ada tombol "Bandingkan dengan kompetitor" → TABEL PILIH-PILIH (pilih produk Aqua + 1-3 kompetitor, kolom harga/kapasitas/tipe pintu/brand berdampingan). Aturan: isi dari data materi; kalau kurang boleh cari sumber eksternal VALID (web resmi/marketplace) dengan SYARAT MODEL ID MATCH PERSIS, dan sumbernya DITANDAI di situs. NOL ngarang angka.
4. **CAPTION 323 FOTO GALERI** pakai MiMo (bukan copy nama file): `xiaomi/mimo-v2.5` via OpenRouter (key di `D:\Secret\openrouter management key.txt`), model OMNIMODAL terverifikasi bisa lihat gambar, harga ~$0,14/1jt token = praktis gratis. Keluaran: `site\data\galeri.json` berisi caption tiap foto ("gambar ini tentang apa"), halaman galeri menampilkannya. Bisa jalan paralel.
5. **POLESAN TAMPILAN + ANIMASI RINGAN** (bukan rombak total): lebih banyak visual dari data (chart/insight), animasi halus (fade/slide) yang TIDAK berat; tampilan harus enak dilihat atasan (portofolio) TAPI praktis dipakai harian (pencarian/ navigasi).
6. **TUJUAN AKHIR**: website harus jadi PENGGANTI GDRIVE buat tim Sharleen — lengkap, semua materi bisa diakses di situ, bukan pajangan. Kalau ada materi Drive yang belum masuk (mis. laporan Warehouse PDF yang gagal unduh — link Drive-nya sudah ada), lengkapi.

## Aturan wajib
- Deploy Pages project ini SUDAH di-ACC Louis malam ini (tercatat `D:\AI\state\ronda\antrian-acc\IZIN-SESI.md`), TAPI konfirmasi sekali ke Louis sebelum tiap deploy.
- Jangan sentuh sistem lain (n8n, ERP, harga, uang, order) — project ini berdiri sendiri.
- Angka/fakta wajib bersumber; nol ngarang; sumber ditampilkan.
- Bahasa Indonesia; jam WIB; verifikasi headless sebelum deploy (0 console error, 0 h-scroll ≤390px, screenshot bukti).
- File >25 MiB tidak bisa di Pages → pakai link Drive (pola sudah ada di `file.html`).
- Setelah deploy, cek live 200 + lapor ke Louis dengan link.