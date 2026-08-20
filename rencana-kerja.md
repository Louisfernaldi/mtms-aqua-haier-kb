# Rencana Kerja — MTMS AQUA HAIER Knowledge Hub (17 Agu 2026 ~22:00 WIB)

## Mode: B Bangun (baru, dari nol — project untuk kakak Louis, Sharleen, MT MTMS AQUA HAIER)

## Masalah / kebutuhan (bahasa bisnis)
Kakak Louis (Sharleen, Management Trainee) punya materi pelatihan di Google Drive (PDF/DOCX/Sheet/foto
onboarding, gudang, pabrik, rotation). Ilmunya belum terstruktur & belum ada tampilan portofolio yang
bisa dipamerkan ke atasan. Solusi: website statis publik (link gratis Cloudflare Pages) yang merangkum
SEMUA materi jadi gudang ilmu + galeri kegiatan + portofolio MT, tetap bisa buka file asli.

## Peta yang dibuka + hasilnya
- `D:\AI\projects\_PETA-PROJECTS.md` → nol kembaran; `ubm-dbp-sidang` cuma jadi referensi gaya (lightbox, dark mode)
- Drive `1gRsY6VlPw2sj8XXFxS1M0sK1DEEGPm5k` → 353 file terunduh (24+145+33+17+132+2), 1 file gagal: `Tugas\Sharleen - Warehouse Visit Report- Management Trainee 2026.pdf` (0 byte, kena throttle Google — RETRY nanti)

## Definisi selesai (cek mesin — semua wajib lolos)
1. Semua file materi Drive ada di `materi-drive\` (353) + laporan MT PDF ≥1KB (retry sukses ATAU tercatat terang gagal)
2. Ekstraksi ilmu: tiap PDF/DOCX/xlsx utama punya catatan teks di `site\data\knowledge\*.json` (≥1 fakta asli per sumber, cross-check ke teks asli)
3. HEIC → JPG (web view), foto galeri per kegiatan
4. Website statis jalan lokal (python http.server): index + halaman kategori + pencarian + lightbox + file asli buka (PDF inline / download)
5. 0 error console, 0 overflow horizontal ≤390px, dark+light kebaca (headless Chrome)
6. Screenshot desktop + HP nempel sebagai bukti
7. Minimal 2 visualisasi (diagram) dari data rotation (mis. benchmark kapasitas/kategori, sebar harga)
8. DEPLOY Cloudflare Pages (ACC Louis malam ini, token `D:\Secret\cloudflare-pages-token.txt`), link live diverifikasi 200, tercatat di deploy-log

## Pola proven yang ditiru
- `ubm-dbp-sidang` (`D:\AI\projects\ubm-dbp-sidang\public\index.html`): lightbox popup gambar (max-height 78vh), dark/light toggle, nav ringkas
- Gaya `bikin-sistem-baru`: iris vertikal tipis, tiap iris bukti sendiri

## Langkah + file yang disentuh (iris vertikal)
| # | Iris (fitur mini utuh) | File | Bukti jalan |
|---|---|---|---|
| 1 | Pipeline materi: HEIC→JPG, OCR foto bertulisan, rename no-ext→pdf | `tools\` | jumlah file web-ready = jumlah inventaris |
| 2 | Ekstraksi ilmu: PDF/DOCX/xlsx/xlsb → catatan terstruktur JSON | `tools\extract_*.py` → `site\data\knowledge\*.json` | ≥1 fakta per sumber, cross-check |
| 3 | Rangka situs: index + navbar + halaman per kategori + footer | `site\index.html` + `site\*.html` | navigasi jalan lokal |
| 4 | Pencarian: index client-side dari knowledge JSON | `site\js\search.js` | query uji ketemu fakta |
| 5 | Galeri foto per kegiatan + lightbox popup | `site\galeri-*.html` + `site\js\lightbox.js` | klik foto → popup |
| 6 | File asli: PDF inline viewer + download link DOCX/xlsx | `site\file.html`? → link langsung | PDF kebuka, xlsx ke-download |
| 7 | Visualisasi 2+: benchmark chart + diagram sebar (SVG murni) | `site\js\charts.js` + halaman rotation | angka dari data asli muncul |
| 8 | Verifikasi headless: 0 console error, 0 h-scroll ≤390px, screenshot 2 ukuran | `tools\verify_site.py` | output mentah nempel |
| 9 | Deploy Cloudflare Pages + verifikasi live 200 | wrangler | link live 200 + deploy-log |

## Aksi yang BUTUH ACC Louis (irreversible)
- ~~Deploy live Cloudflare Pages~~ → **ACC DIBERI LOUIS 17 Agu 2026 (~21:45 WIB, tercatat IZIN-SESI.md)**: "ACC deploy malam ini" + "langsung deploy kalau bisa kan aman ga nyentuh sistem gua cn buat web doank". Lingkup: project Pages MTMS AQUA HAIER saja.
- Ngirim link ke atasan Sharleen → BUKAN kita, Louis yang kirim
- Hapus materi asli → tidak akan dilakukan

## Penjaga anti-kambuh / verifikasi akhir
- Retry laporan MT PDF menjelang akhir (jeda >30 menit dari throttle)
- Screenshot + console log headless nempel di `evidence\`
- Cross-check 2-3 fakta tiap PDF utama → teks asli muncul di website

## Asumsi yang diambil (karena info bolong) + tanda
- OCR: pakai Windows OCR (WinRT) — kalau gagal, foto bertulisan dicatat & foto tetap masuk galeri (ASUMSI)
- Konten Sheets: diambil sebagai data tabel + kesimpulan manual Claude (data asli, bukan ngarang) (ASUMSI)
- Gaya visual: bersih/profesional, aksen biru-aqua (identitas merek AQUA), dark mode opsional (ASUMSI)
- Bahasa situs: Indonesia (audiens atasan lokal) (ASUMSI)

## Keputusan yang paling ga diyakini (tiang rapuh — tantang SEKARANG)
1. **OCR foto**: nol tesseract lokal; Windows OCR via WinRT belum diuji. Kalau gagal → foto tetap masuk galeri tanpa OCR (konten tetap kaya dari PDF/DOCX). Risiko: foto papan materi kehilangan isi teks.
2. **Satu halaman vs multi-halaman**: pilih multi-halaman (ringan, bisa di-`curl` per halaman). Risiko: search lintas halaman harus lewat index JSON (sudah direncanakan).
3. **Charts murni SVG tulisan tangan vs lib chart**: pilih SVG murni (nol dependensi = nol risk CDN mati di Pages). Risiko: lebih banyak kerja, tapi terkendali.
4. **Nama project Pages**: `mtms-aqua-haier-kb` → subdomain `.pages.dev` otomatis. Bisa diubah kapan pun (reversible).
5. **Zero-dependency murni** (tanpa framework): semua JS vanilla. Risiko rendah tapi pastikan di-verify headless.
