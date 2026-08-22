# Tiket 11 — Integrasi nav & beranda [BISA-DIBATALIN · ANTRE SESI SEBELAH]
> Induk: `..\..\SPEC-galeri-insight-engine-v1.md` · codex-fit: ya (edit nav mekanis)

**Tujuan:** Masukkan link halaman baru (Pasar, Benchmark, Strategi, Poster) ke nav SEMUA halaman + kartu ringkas di index.html. ⚠️ Tiket ini ANTRE: baru boleh jalan setelah sesi Produk/Kompetitor kelar & deploy (cek PROGRES.md + mtime). Nav edit menyentuh berkas milik dia (produk/kompetitor/index/style.css).

**Definisi selesai (cek mesin):**
- Semua halaman html punya link nav lengkap (grep hitung = jumlah halaman).
- Headless index + 1 halaman lama: 0 error, 0 h-scroll @390px.
- Sesi sebelah udah kelart tercatat di PROGRES.md (prasyarat, bukan hasil).

**Cara verifikasi:** `python tools\verify_site.py --page index.html` + grep nav.

**File yang disentuh:** `site\index.html`, `site\*.html` (nav semua halaman), `site\css\style.css` (hanya kalau perlu), `site\js\data.js` (regen fallback)

**Dependensi:** tiket 02, 05, 07, 08, 09 + sesi sebelah KELAR

```estafet
id: 11
status: belum-mulai
owner: codex
verifier: claude-mandor
depends_on: [02, 05, 07, 08, 09]
gerbang_acc:
boleh_otomatis:
  - "edit nav + verifikasi headless offline"
stop_butuh_louis: []
cek_selesai:
  - "python tools/verify_site.py --page index.html"
file_disentuh:
  - "site/index.html"
  - "site/*.html"
  - "site/css/style.css"
file_dibaca_doang:
  - "tools/verify_site.py"
```
