# Visual Audit Plan — MTMS AQUA HAIER Knowledge Hub

> **STATUS: PLAN ONLY — TAHAN EKSEKUSI**  
> Dibuat: 20 Agu 2026 18:30 WIB (mandor). Belum ada file `site/` yang diubah. Semua temuan di bawah butuh ACC Louis sebelum fix.  
> Scope: `D:/AI/projects/mtms-aqua-haier-kb/site` — 9 halaman HTML (index, produk, kompetitor, induksi, rotasi, proses, galeri, file, login)  
> Metode: juri-tampilan (CEO 50an berkacamata + Desainer Pro) + cek 5 aspek per halaman. Screenshot real via Playwright Chromium.

**Cara baca:** Tiap baris `| Halaman | Aspek | Severity | Temuan | Usulan fix | Screenshot |` adalah 1 tiket kecil siap eksekusi. **P0 = pusing/susah baca → harus dibenerin sprint ini**, P1 = kurang enak, P2 = nice-to-have.

---

## 0. Ringkasan Prioritas

| Severity | Jumlah | Arti | Contoh pemicu |
|----------|--------|------|---------------|
| **P0** | **21** | Harus dibenerin dulu — sales/CS gagal pakai atau mata sakit | font <11px, thumb crop, tabel tanpa sticky, 74 sel kosong, nav numpuk, placeholder biru massal |
| **P1** | **42** | Ganggu workflow — bikin lambat / tidak profesional | kontras muted 4.2:1, hierarki flat, chip <44px, legend inkonsistensi, empty tanpa CTA |
| **P2** | **16** | Polish — backlog | border dobel, divider, shadow, dark-token, caption |
| **Total** | **79** | — | — |

**Breakdown per area pekerja (mandor):**

| # | Area (pekerja) | Halaman utama | Temuan P0/P1/P2 | Status juri |
|---|----------------|---------------|----------------|-------------|
| 1 | Kompetitor tabel 32 baris / 74 sel kosong | `kompetitor.html` | 6 / 10 / 2 (18) | CEO 4.4, Desainer 4.8 — GAGAL |
| 2 | Produk/katalog grid foto | `produk.html` | 3 / 9 / 2 (14) | CEO 4.0, Desainer 5.0 — GAGAL |
| 3 | Perbandingan/detail (modal, filmstrip, tabel) | `produk.html` modal + `kompetitor` tabel + `rotasi` chart | 5 / 7 / 2 (14) | CEO 5.3, Desainer 5.0 — BELUM LULUS |
| 4 | Index/landing + nav/header/footer | `index.html` (+ konsistensi induksi/rotasi/galeri/file) | 3 / 8 / 4 (15) | CEO 5.8, Desainer 5.5 — PERLU PERBAIKAN |
| 5 | Komponen umum (overlay, tombol, toast, search, lightbox) | lintas halaman | 4 / 8 / 6 (18) | CEO 6.1, Desainer 5.4 — PERLU PERBAIKAN |

**Urutan fix rekomendasi (habis ACC):** P0 dulu (21) → `kompetitor.html` sticky + font + empty, `produk.html` placeholder + sticky chip + thumb contain, `index` drawer mobile, `modal` wide + harga hero, `overlay` seksi. Baru P1, lalu P2.

---

## 0.1 Skor Juri per Halaman (0-10, ambang lulus ≥8 + nol keluhan “harus menyipitkan” + cek-kontras lulus)

| Halaman | CEO berkacamata (keterbacaan & nyaman mata) | Desainer Pro (kontras/spacing/hierarchy) | Komentar 1 kalimat | Vonis |
|---------|-----------------------------------------------|------------------------------------------|--------------------|-------|
| `kompetitor.html` | **4.4/10** — “harus lepas kacamata baca fitur 10.8px, 74 kotak putus bikin capek, AQUA ikut ke-scroll” | **4.8/10** — header tidak sticky, 900px sempit, gradient duplikat, cover crop | Paling pusing aspek 1+3+5 | **GAGAL** |
| `produk.html` (katalog) | **4.0/10** — “meta 13px + badge 11px musti disipitkan, 30 kartu biru numpuk tanpa paging” | **5.0/10** — hierarki harga flat, gap 4px sesak, placeholder menipu | Belum layak naik | **GAGAL** |
| Perbandingan/detail (modal & filmstrip) | **5.3/10** — “harga tenggelam, modal kecil buang 70% ruang, scroll panjang” | **5.0/10** — thumbs 56px under-scale, divider hilang, empty biru pucat | Scatter chart tooltip hilang | **BELUM LULUS** |
| `index.html` + header/footer | **5.8/10** — “deskripsi 0.88rem abu harus disipitkan, nav 8 link numpuk 2 baris + 6 kartu rame” — **perlu disipitkan: YA** | **5.5/10** — hero gradient pucat, ghost hilang, emoji murah, foto 170px crop | Konsisten di semua halaman | **PERLU PERBAIKAN** |
| Komponen umum | **6.1/10** — “Edit/Hapus 9.9px takut kepencet Hapus, input 0.8rem kekecilan” | **5.4/10** — 3 backdrop beda opacity, spacing tidak 4pt, kontras <3:1 | Blocking karena lintas halaman | **PERLU PERBAIKAN** |
| `induksi.html` | **5.6/10** — “blok `ik-seg-txt` 1.35rem oke tapi bullet 0.88rem muted sesak, fridge icon 52px kecil” | **5.7/10** — gap 10px rapat, card `ik-sub` 150px sempit, warna chip kontras rendah | Mirip produk — perlu naik font + spacing | **PERLU PERBAIKAN** |
| `rotasi.html` | **5.5/10** — “chart title 1rem vs sub 0.8rem muted, bar label % kecil, scatter dot 7px tanpa label” | **5.2/10** — chart-wrap padding 18px sesak, legend flex gap 16px longgar, grid 640px overflow | Tooltip & dot perlu besar | **PERLU PERBAIKAN** |
| `proses.html` | **6.0/10** — “timeline `tl-title 1rem` ok tapi `tl-detail 0.88rem muted` kecil, badge 0.72rem nyempit” | **5.8/10** — `tl-step gap 14px` ok tapi `tl-num 34px` vs card padding 16px imbalance | Timeline paling mending | **PERLU PERBAIKAN RINGAN** |
| `galeri.html` | **5.2/10** — “gallery 150px/110px ok tapi figcaption 0.72rem harus disipitkan, 323 foto tanpa pagination” | **4.9/10** — grid auto-fill 150px rapat, lightbox prev/next 44px mepet 12px, no skeleton” | Empty/loading paling parah | **GAGAL** |
| `file.html` | **5.7/10** — “file-list 0.9rem line-height 1.6 ok tapi `sz` muted + `[Drive]` biru tipis, preview btn 0.78rem kecil” | **5.6/10** — `li flex-wrap gap 12px padding 10px 4px` dempet, hover `bg-soft` tipis | List panjang tanpa divider tegas | **PERLU PERBAIKAN** |
| `login.html` | **6.5/10** — “input 1rem ok, tapi h1 1.3rem vs p 0.9rem muted kontras rendah, btn 1rem ok” | **6.2/10** — card 360px/32px padding ok, shadow 0.2 ok, no logo besar | Paling bersih, minor polish | **PERLU POLISH** |
| **Rata-rata site** | **5.3/10** | **5.2/10** | Semua di bawah ambang 8 | **TAHAN RILIS** |

> Semua skor di atas dari juri buta-niat (tidak dikasih tau niat pembuat), nilai dari screenshot hidup + baca `site/css/style.css` baris terkait. Kriteria 5 “Memudahkan User” semua = **GAGAL** (butuh 1 detik bandingin harga/kapasitas).

---

## 0.2 Bukti Screenshot (Playwright Chromium, fullPage)

| Halaman | Desktop 1280×800 | Mobile 390×844 | Lain |
|---------|-----------------|----------------|------|
| index | `rencana/screenshots/index-desktop.png` (539KB) | `index-mobile.png` (404KB) | — |
| produk | `produk-desktop.png` (765KB) | `produk-mobile.png` (764KB) | `produk-modal-desktop.png` (1.4MB) |
| kompetitor | `kompetitor-desktop.png` (1.56MB) | `kompetitor-mobile.png` (773KB) | `kompetitor-overlay-desktop.png` (1.5MB) |
| induksi | `induksi-desktop.png` (464KB) | `induksi-mobile.png` (471KB) | — |
| rotasi | `rotasi-desktop.png` (443KB) | `rotasi-mobile.png` (376KB) | — |
| proses | `proses-desktop.png` (214KB) | `proses-mobile.png` (198KB) | — |
| galeri | `galeri-desktop.png` (1.23MB) | `galeri-mobile.png` (305KB) | — |
| file | `file-desktop.png` (163KB) | `file-mobile.png` (147KB) | — |
| login | `login-desktop.png` (21KB) | `login-mobile.png` (18KB) | — |
| komponen | — | — | `search-overlay-desktop.png` (469KB) |

**Jam bukti:** 20 Agu 2026 11:30 WIB, `python shot_mtms.py` + `sync_playwright`. Server `localhost:4321` serve `site/`. Tiap halaman tunggu `networkidle + 2s` biar `MTMS_DATA` render. Verifikasi: semua file ada, `ls rencana/screenshots` 21 file.

---

## Mandor — Pembagian Porsi (re-fresh §9 Pabrik mini)

**Aturan yang dipakai:** `re-fresh` §9 — maks **4 pekerja paralel**, tiap pekerja **max-iter 3** (mentok = parkir + lapor), **2 tugas yang nyentuh-TULIS file sama WAJIB antri** (1 worktree, berurutan). Pekerja `codex` untuk ketik berat, `vision` untuk nilai visual. Irreversible (deploy/harga/ship/kirim customer/DB) = parkir draft, STOP.

| # | Judul halaman/area | File utama | Kenapa paralel / urut | Tulis file |
|---|--------------------|------------|------------------------|------------|
| 1 | Kompetitor tabel 32×5 + 74 kosong | `kompetitor.html` | **Paralel batch-1** — read-only, tidak sentuh file | tidak → aman |
| 2 | Produk/katalog grid foto | `produk.html` | **Paralel batch-1** — read-only, beda file | tidak |
| 3 | Perbandingan/detail (modal, filmstrip, chart) | `produk.html` modal + `rotasi.html` | **Paralel batch-1** — read-only, butuh ngerti, pakai vision | tidak |
| 4 | Index/landing + nav/header/footer | `index.html` | **Paralel batch-1** — read-only, cek konsistensi lintas halaman | tidak |
| 5 | Komponen umum (overlay, tombol, toast, search, lightbox) | lintas `site/css/style.css` + `kompetitor.html` + `produk.html` | **Antri → tunggu 1 slot batch-1 kosong** (max 4 penuh) + merge tulis **antri** setelah semua selesai | Ya → **1 penulis** gabung ke `rencana/visual-audit-plan.md` (antri, bukan barengan) |

**Sebelum sebar:** mandor screenshot semua halaman (21 file) dulu biar pekerja punya bukti. **Sesudah audit:** mandor gabung temuan → 1 file plan (ini). **Gerbang ACC:** semua fix disiapkan sebagai draft, **TIDAK dieksekusi** sampai Louis ketok. Deploy live = **STOP** (hard-stop #1 + #6).

**Alat:** ketik berat → `codex` (tidak dipakai di fase plan, read-only), nilai visual → `vision` (5 subagen vision di atas). Verifikasi → mandor cek ulang screenshot + `read` css baris.

---

## 1. kompetitor.html — Tab per kategori, tabel AQUA vs 5 brand (32 baris, 74 sel kosong)

**Skor juri:** CEO 4.4 / Desainer 4.8 (lihat §0.1). **Screenshot:** `kompetitor-desktop.png` 1280 + `kompetitor-mobile.png` 390 + `kompetitor-overlay-desktop.png`.

| Halaman | Aspek | Severity | Temuan (1 kalimat) | Usulan fix | Screenshot path |
|---------|-------|----------|--------------------|------------|-----------------|
| kompetitor.html | Keterbacaan teks | **P0** | `.comp-fitur-list li 0.68rem (10.88px) line-height 1.35 #4d6b7a` di cell gradient pastel → gagal WCAG AA, CEO harus menyipitkan. | Naikkan ke `0.75rem line-height 1.5 color var(--text) #12303f`, clamp 3 baris + tooltip `style.css:32` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Keterbacaan teks | **P0** | `.comp-meta 0.7rem (11.2px) white-space:nowrap` “120 L · Rp …” terpotong di kolom 16.4% ≈147px. | Pecah 2 baris: kapasitas di atas, harga `0.78rem bold var(--accent-dark)`, hapus `nowrap` `style.css:30-31` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Keterbacaan teks | **P0** | Tombol `.comp-row-actions button 0.62rem (9.92px) 2px 8px` hit-area <24px, risiko salah pencet Hapus. | `font 0.75rem padding 6px 12px min-height 32px gap 6px` `style.css:37` + ikon ✎/🗑 | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Keterbacaan teks | **P1** | Header `th 0.78rem` + body `0.82rem` + `.comp-model-name 0.82rem` kontras tipis, tidak sticky saat scroll 32 baris. | `th 0.85rem weight 800 bg var(--accent-dark) color #fff position:sticky top 60px` `style.css:699` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Keterbacaan teks | **P1** | `.comp-brand-badge 0.58rem (9.28px)` pill di dalam cell tidak terbaca tanpa zoom. | Naikkan ke `0.68rem padding 3px 10px`, pindah ke header kolom atau di atas thumb `style.css:23` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Proporsi & kualitas gambar | **P1** | `.comp-thumb max 110px (80px mobile) 3/4 cover` memotong kulkas SBS/2 pintu atas-bawah. | Ganti `aspect 4/5 object-fit:contain bg #fff padding 4px` + srcset 1x/2x `style.css:20+718` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Proporsi & kualitas gambar | **P1** | Placeholder `dummyimage.com/400x533` warna solid per brand terlihat prototipe, blur saat cover. | Ganti outline SVG kulkas + teks `Foto belum ada — BRAND MODEL`, bukan dummy warna | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Proporsi & kualitas gambar | **P2** | Thumb `border 1px` di atas cell gradient bikin garis dobel. | Hapus border, ganti `box-shadow 0 1px 4px rgba(0,0,0,.08)` `style.css:718` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Hierarki & spacing | **P0** | 32 baris tanpa sticky header & filter → sales bandingkan harus scroll 4 layar, hilang konteks. | `th sticky top 60px`, `comp-cat-header sticky top 58px` + chip filter kategori di atas tabel | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Hierarki & spacing | **P0** | `min-width 900px (700 mobile) fixed 18%/16.4%` → 1280 whitespace, 390 AQUA ikut ke-scroll, tanpa indikator swipe. | `min-width 1080 desktop`, AQUA `sticky left:0 shadow`, fade kanan, fallback card <640px `style.css:698` | `rencana/screenshots/kompetitor-mobile.png` |
| kompetitor.html | Hierarki & spacing | **P1** | `section margin 36px` terlalu rapat antar kategori, wrapper tanpa card. | `margin 48px`, wrapper `bg-card border radius 12 shadow` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Hierarki & spacing | **P1** | `th/td 8px 6px` vs css `10px 8px` inkonsisten, mepet thumb + bullet. | Standar `12px 10px`, `gap 6px` di `comp-model-info` `style.css:717` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Warna/accent | **P1** | Cell gradient LG/Midea/Sharp pink `#fde8e8` vs Polytron/Samsung biru `#e8eefc` duplikat, tidak semantik. | Hapus gradient, `bg #fff`, hanya `border-left 3px` warna brand `style.css:707-714` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Warna/accent | **P1** | Legend `AQUA #0066CC` ≠ badge `var(--accent) #0097d6` — token bocor. | Samakan AQUA `#0097d6`, dot 12px, legend `0.85rem 600 sticky` `kompetitor.html:92` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Empty/loading state | **P0** | 74 sel dashed `+ Tambah Model 0.72rem` repetitif → 45% tabel bolong, dikira rusak. | Ghost subtle `border transparent bg var(--bg-soft)` hover baru accent; opsi collapse brand kosong | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Empty/loading state | **P1** | `#comp-empty` hanya `<p>Tidak ada data…</p>` tanpa ilustrasi/CTA. | Ilustrasi outline 80px + CTA `Tambah Model AQUA pertama` primary | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor.html | Empty/loading state | **P1** | Overlay `rgba(0,0,0,.5)` tanpa blur, input 0.85rem kecil, `foto-preview 120x160` crop. | `rgba(6,16,22,.6)+blur(2px)`, lock body, `btn-save 44px`, preview `contain+placeholder` `style.css:42-59` | `rencana/screenshots/kompetitor-overlay-desktop.png` |
| kompetitor.html | Empty/loading state | **P2** | Toast `bottom 24px left50%` durasi 2.2s hilang sebelum PUT selesai, tutup thumb di mobile. | `top-right 16px`, 3.5s/6s, ikon ✓/✕ + X, `role=status` `kompetitor.html:530` | `rencana/screenshots/kompetitor-overlay-desktop.png` |

---

## 2. produk.html — Katalog (foto produk, grid)

**Skor juri:** CEO 4.0 / Desainer 5.0. **Screenshot:** `produk-desktop.png` 1280 + `produk-mobile.png` 390.

| Halaman | Aspek | Severity | Temuan | Usulan fix | Screenshot |
|---------|-------|----------|--------|------------|------------|
| produk.html | Keterbacaan teks | **P0** | `.pk-meta 0.82rem + .pk-cat 0.75rem + .badge 0.7rem` terlalu kecil, mobile harus disipitkan. | `.pk-meta→0.88rem/1.5`, `.pk-cat→0.8rem`, `.badge→0.75rem 600` `css:212,215,258` | `rencana/screenshots/produk-mobile.png` |
| produk.html | Keterbacaan teks | **P1** | `pk-cap/pk-meta/p.sec-sub #4d6b7a` di putih kontras ~4.6:1 tipis untuk 13px. | Gelapkan `--text-muted→#3e5f6e` atau `color:var(--text)` untuk meta primer | `rencana/screenshots/produk-desktop.png` |
| produk.html | Keterbacaan teks | **P1** | `pk-model 1.05rem` vs `pk-cap 0.9rem` vs `pk-price 0.92rem` beda tipis, harga tidak hero. | `pk-model→1.1rem 700`, `pk-price→1.0rem 800 letter-spacing -0.2px` `css:213,225` | `rencana/screenshots/produk-desktop.png` |
| produk.html | Proporsi & kualitas gambar | **P0** | ~70% kartu `pk-thumb pk-noimg #eaf3fa + ❄️ 3rem` kesan katalog belum jadi/bug. | SVG siluet kulkas + label `Belum ada foto · AQR-XXX 0.8rem`, `1/1 dashed` `css:221-224` | `rencana/screenshots/produk-desktop.png` |
| produk.html | Proporsi & kualitas gambar | **P1** | `pk-thumb 4/3 cover` motong kulkas tinggi, kepala terpotong di grid 260px. | `3/4 contain bg #f4f8fb padding 8px` `css:216-220` | `rencana/screenshots/produk-desktop.png` |
| produk.html | Proporsi & kualitas gambar | **P1** | Tidak ada shimmer saat `fetch api/produk` — grid putih lama lalu muncul serentak. | Skeleton 6× `pk-card.skeleton` shimmer sampai `render()` selesai `produk.js:355` | `rencana/screenshots/produk-mobile.png` |
| produk.html | Hierarki & spacing | **P0** | `pk-grid minmax(260px)` 3 kol 1280 tanpa paging → stitched >8000px, scroll 20 viewport. | Sticky `.pk-chips top 60px z-index5 bg var(--bg)` + paginasi 12/24 + counter tegas `produk.js:371` | `rencana/screenshots/produk-mobile.png` |
| produk.html | Hierarki & spacing | **P1** | `.pk-card gap 4px` sesak, badge-wrap numpuk dekat pk-cat. | `gap 6px + pk-card-top mb 6px + thumb my 10px` `css:208` | `rencana/screenshots/produk-desktop.png` |
| produk.html | Hierarki & spacing | **P1** | Chips `6px 14px 0.85rem <44px` wrap 3 baris di 390, susah tap. | `9px 16px min-height36 gap10` `css:196-199` | `rencana/screenshots/produk-mobile.png` |
| produk.html | Hierarki & spacing | **P2** | `ringkasan-blok → stat-card` tanpa divider, `h2.sec 1.45rem` vs `hero-mini 1.55rem` beda tipis. | `h2.sec border-left 4px accent padding-left10` | `rencana/screenshots/produk-desktop.png` |
| produk.html | Warna/accent | **P1** | Chips idle `bg-card #fff border #d8e5ee` pucat, tidak terlihat tappable di atas foto. | Idle `bg-soft border #cfe0ee` + hover `accent-soft` | `rencana/screenshots/produk-desktop.png` |
| produk.html | Warna/accent | **P2** | Badge 5 warna pastel noise, tidak signal. | 2 warna: accent untuk Inverter/Flagship, netral `#eef2f6` lain `css:262-267` | `rencana/screenshots/produk-desktop.png` |
| produk.html | Empty/loading state | **P1** | Filter 0 hasil hanya `<p>Tidak ada produk…</p>` tanpa saran. | Ilustrasi 🔍 + `Tidak ada hasil "Multidoor"` + `Reset→Semua (74)` `produk.js:365` | `rencana/screenshots/produk-desktop.png` |
| produk.html | Empty/loading state | **P1** | Placeholder tanpa CTA upload, CS tidak tahu bisa `openEdit`. | Teks `Ketuk untuk upload foto 0.78rem` hanya saat `MTMS_DATA_LIVE=true` → `openEdit()` | `rencana/screenshots/produk-desktop.png` |

---

## 3. Perbandingan/detail — Modal produk, tabel & filmstrip

**Skor juri:** CEO 5.3 / Desainer 5.0. **Screenshot:** `produk-modal-desktop.png` + `kompetitor-desktop.png` + `rotasi-desktop.png`.

| Halaman | Aspek | Severity | Temuan | Usulan fix | Screenshot |
|---------|-------|----------|--------|------------|------------|
| produk.html modal `.pk-modal-box` | Hierarki & spacing | **P0** | Box max 640px di 1280, galeri+tabel ditumpuk vertikal, ruang gelap 70% terbuang. | `max-width 980px` + grid 2-kol `42%|58%` `css:287` | `rencana/screenshots/produk-modal-desktop.png` |
| produk.html modal galeri `.pk-gal-stage` | Proporsi & kualitas gambar | **P0** | `pk-gal-img max 50vh width auto` kecil, thumbs 56px tidak bedakan material. | `width100% height360 contain` + thumbs 68px border3 accent | `rencana/screenshots/produk-modal-desktop.png` |
| produk.html modal harga | Keterbacaan teks | **P0** | Harga di baris tabel `Harga pasar 0.9rem` tenggelam dengan “Daya 42W”. | Hero `Rp 11.1 jt 1.4rem bold accent-dark` di atas tabel | `rencana/screenshots/produk-modal-desktop.png` |
| produk.html modal fitur | Hierarki & spacing | **P1** | Dua `h4 Fitur Unggulan` + `Keunggulan` tanpa divider, `pk-fitur` & `pk-benefit` dempet. | Divider `border-top` + gap24, hapus duplikasi `produk.js:300-306` | `rencana/screenshots/produk-modal-desktop.png` |
| produk.html modal kontrol | Warna/accent | **P1** | Close `× 1.8rem` tanpa bg hilang di putih, nav `rgba(6,16,22,.45)` hilang di foto putih. | Circle 32px `bg-card border shadow`, nav `#12303F 0.72 SVG 20px` | `rencana/screenshots/produk-modal-desktop.png` |
| produk.html modal loading | Empty/loading state | **P1** | Tidak ada skeleton, `fotos==0` kosong, spec `—` tanpa konteks. | Shimmer 360px+3 thumbs, `—`→`Belum ada data · cek PDF` | `rencana/screenshots/produk-modal-desktop.png` |
| produk.html grid `.pk-grid` | Empty/loading state | **P0** | >50% kartu `pk-noimg` box pucat dikira bug. | Outline dashed + `Foto menyusul — AQR-xxx 0.8rem` + shimmer | `rencana/screenshots/produk-desktop.png` |
| produk.html tabel Ringkasan | Keterbacaan teks | **P1** | Tabel 4 kol `0.9rem` padat, harga tidak rata kanan, sumber ganggu scan. | `text-align:right tabular-nums`, sumber `0.72rem italic 0.7` | `rencana/screenshots/produk-desktop.png` |
| produk.html filmstrip `.pk-filmstrip` | Hierarki & spacing | **P1** | Card 340px snap tanpa panah/gradient, tidak tahu ada 5 kartu kanan. | Fade 40px + `‹ ›` overlay + `●●○ 1/5` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor `.comp-full-table` | Keterbacaan teks | **P0** | `comp-fitur 0.65rem + meta 0.7rem <11px` + kolom tidak sticky saat scroll 900px. | `0.78rem 1.5`, sticky left+top shadow `css:718-720` | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor warna | Warna/accent | **P1** | Gradient LG/Midea merah & Polytron/Samsung biru tidak distinct, hanya AQUA left-border. | Hapus gradient, `border-top 3px brand` per kol | `rencana/screenshots/kompetitor-desktop.png` |
| kompetitor gambar | Proporsi & kualitas gambar | **P1** | Thumb 130px 3/4 cover crop, nama `break-word` 3 baris. | `110px contain bg-soft`, `line-clamp2 ellipsis + title` | `rencana/screenshots/kompetitor-desktop.png` |
| rotasi chart scatter | Proporsi & kualitas gambar | **P2** | Dot ~7px tanpa label, sumbu `0t 5t` ambigu. | Dot 10px stroke2, tooltip `model+Rp+L`, legenda 0.78rem | `rencana/screenshots/rotasi-desktop.png` |
| modal scroll | Hierarki & spacing | **P2** | Box+body double overflow, footer-tabs tidak dirender. | Hanya body `max-height calc(80vh-140px)` scroll, aktifkan tabs `Detail|Perbandingan` | `rencana/screenshots/produk-modal-desktop.png` |

---

## 4. Index/landing + navigasi/header/footer

**Skor juri:** CEO 5.8 / Desainer 5.5 (header konsisten di semua halaman). **Screenshot:** `index-desktop.png` + `index-mobile.png`.

| Halaman | Aspek | Severity | Temuan | Usulan fix | Screenshot |
|---------|-------|----------|--------|------------|------------|
| index.html | Hierarki & spacing | **P0** | `.nav flex-wrap` 8 link+2 btn numpuk 2 baris di 390, tanpa hamburger. | `.nav-links{overflow-x:auto;flex-wrap:nowrap}` + drawer `☰` ≤640px `css:45-48` | `rencana/screenshots/index-mobile.png` |
| index.html | Empty/loading state | **P0** | Galeri Manufacturing 78 placeholder `#eaf3fa` tanpa teks/spinner — dikira error. | Shimmer + `Foto belum dimuat — tarik ulang` | `rencana/screenshots/galeri-desktop.png` |
| index.html | Proporsi & kualitas gambar | **P0** | `.bp img 170px` crop brutal, gedung/Excel blur. | `200px 16/10 object-position:center`, screenshot `contain+bg putih` `css:341` | `rencana/screenshots/index-desktop.png` |
| index.html | Keterbacaan teks | **P1** | `.nav-links a 0.9rem #4d6b7a` di putih kontras ~4.2:1 tipis. | `0.95rem #2f4957 padding 7px 12px` `css:54` | `rencana/screenshots/index-desktop.png` |
| index.html | Keterbacaan teks | **P1** | `kat-card p 0.88rem muted` 6 kartu bikin lelah. | `0.93rem 1.65 #3d5a6b clamp3` `css:112` | `rencana/screenshots/index-desktop.png` |
| index.html | Keterbacaan teks | **P1** | `hero p muted` di gradient `accent-soft→#fff` pudar. | `color #305462 0.98rem max600` `css:79` | `rencana/screenshots/index-desktop.png` |
| index.html | Warna/accent | **P1** | Ghost `1.5px border` hilang di hero pucat. | `2px + bg rgba(255,255,255,.9) shadow 0 1 6 rgba(0,151,214,.15)` `css:85` | `rencana/screenshots/index-desktop.png` |
| index.html | Proporsi & kualitas gambar | **P1** | Emoji `ico 1.8rem` murah vs brand premium. | SVG 28px monokrom `accent-dark` bulat `44×44 accent-soft` `css:110` | `rencana/screenshots/index-desktop.png` |
| index.html | Proporsi & kualitas gambar | **P1** | `brand-logo 22px`, `MTMS 0.85rem 0.75` kalah saing Haier. | `logo 26px`, `MTMS 0.95rem 700 #12303f` `css:50-51` | `rencana/screenshots/index-desktop.png` |
| index.html | Hierarki & spacing | **P1** | Ritme `26→40→16→34px` tidak skala 24/32. | `stats 32, h2.sec 32 0 8, sec-sub mb20` `css:88-97` | `rencana/screenshots/index-desktop.png` |
| index.html | Warna/accent | **P1** | Monoton biru semua (stat, h3, go, tag) tanpa Haier Red CTA. | CTA `btn` pakai `#E60012`, stats tetap biru | `rencana/screenshots/index-desktop.png` |
| index.html | Hierarki & spacing | **P2** | `hero 44px 16px 36px` sempit di 1280, h1 2rem tidak napas. | `56px 32px 44px, h1 2.2rem` desktop `css:69` | `rencana/screenshots/index-desktop.png` |
| index.html | Warna/accent | **P2** | `h3` kat-card `#12303f` vs brand-fact `#0073a3` inkonsisten. | Samakan `kat-card h3 accent-dark` | `rencana/screenshots/index-desktop.png` |
| index.html | Keterbacaan teks | **P2** | Footer `0.85rem muted` rapat di mobile, `brand-facts 0.9rem` mini. | `0.88rem line1.6 padding24` | `rencana/screenshots/index-desktop.png` |
| index.html | Keterbacaan teks | **P2** | Caption `bp span 0.82rem` gradient bawah kontras turun di ujung. | `0.88rem 600 text-shadow 0 1 2 rgba(0,0,0,.4)` `css:342-345` | `rencana/screenshots/index-desktop.png` |

> Konsistensi: header/footer sama di `induksi-desktop.png`, `rotasi-desktop.png`, `galeri-desktop.png`, `file-desktop.png` — bug nav & muted terbawa semua halaman.

---

## 5. Komponen umum — Overlay, tombol, toast, search, lightbox

**Skor juri:** CEO 6.1 / Desainer 5.4 — blocking karena lintas halaman. **Screenshot:** `kompetitor-overlay-desktop.png` + `search-overlay-desktop.png` + `produk-modal-desktop.png`.

| Komponen | Aspek | Severity | Temuan | Usulan fix | Screenshot |
|----------|-------|----------|--------|------------|------------|
| `.comp-edit-overlay` + card | Hierarki & spacing | **P0** | Card 520px 7 field tanpa grup, gap label→input 4px sesak. | `gap12` per field + 3 seksi + `border-top padding12` | `rencana/screenshots/kompetitor-overlay-desktop.png` |
| `.comp-edit-overlay` | Warna/accent | **P0** | Backdrop `rgba(0,0,0,.5)` ≠ `search .58` ≠ `pk-modal .7` inkonsistensi. | Samakan `rgba(6,16,22,.64) blur4` semua overlay | `rencana/screenshots/kompetitor-overlay-desktop.png` |
| `.comp-edit-card` label+input | Keterbacaan teks | **P0** | Label `0.8rem` + input `0.85rem` kekecilan untuk mata 45+ di toko. | Label `0.85rem 600 1.5`, input `0.95rem 10px 12px` + focus ring 2px accent | `rencana/screenshots/kompetitor-overlay-desktop.png` |
| `.comp-edit-card` preview | Proporsi & kualitas gambar | **P1** | Preview `120x160 cover` crop 3:4, upload DataURL tanpa compress pecah. | `140px 3/4 contain bg-soft` + compress max800 JPEG0.8 | `rencana/screenshots/kompetitor-overlay-desktop.png` |
| `.comp-edit-card` actions | Hierarki & spacing | **P1** | `Batal/Simpan 8px 18px` tanpa × close, klik backdrop close tanpa konfirmasi. | × 32px, Batal 92px, Simpan 110×40, konfirmasi dirty | `rencana/screenshots/kompetitor-overlay-desktop.png` |
| `.search-overlay` | Warna/accent | **P1** | `z-index 90` di bawah `pk-modal 95` → search ketutup modal, tanpa blur. | `z-index120 + blur6 + rgba(6,16,22,.58)` `css:150` | `rencana/screenshots/search-overlay-desktop.png` |
| `.search-box` input | Keterbacaan teks | **P1** | Placeholder `#999 2.8:1` gagal WCAG, tanpa ikon. | `placeholder var(--text-muted) 0.85` + 🔍 18px `pl42` `css:159` | `rencana/screenshots/search-overlay-desktop.png` |
| `.search-results` `.r` | Hierarki & spacing | **P1** | Hasil `10px 12px` tanpa beda judul/isi, hover tipis, no focus. | Judul 1rem 700, isi 0.9rem clamp2, `focus-visible outline2 accent bg-accent-soft` | `rencana/screenshots/search-overlay-desktop.png` |
| `.search-results` empty | Empty/loading state | **P1** | Empty cuma teks, no spinner saat `loadKbIndex()` 14 file, no saran. | Ilustrasi 48px + chips `garansi,SBS,GFK` + spinner 12px | `rencana/screenshots/search-overlay-desktop.png` |
| `.icon-btn` Cari/Mode | Keterbacaan teks | **P1** | `6px 12px 0.9rem bg #eaf3fa` kontras 1.4:1, hit <44px. | `8px 14px 36×44 border1.5px aria-label` `css:60` | `rencana/screenshots/index-desktop.png` |
| `.btn` ghost | Warna/accent | **P2** | Hover `#0073a3` terlalu gelap, ghost hilang di hero gradient. | Ghost di hero `bg #fff shadow 0 1 6 rgba(0,0,0,.06)` `css:85` | `rencana/screenshots/index-desktop.png` |
| `.comp-row-actions` | Keterbacaan teks | **P0** | `2px 8px 0.62rem ~38px` muted `#52616e` di mobile harus pinch. | `6px 10px 0.78rem 32×48 + ✎/🗑` | `rencana/screenshots/kompetitor-desktop.png` |
| `.comp-add-btn/cell` | Hierarki & spacing | **P2** | `+ Tambah Model dashed 1px` halus, hilang di 6 kol. | `1.5px dashed accent bg-accent-soft 6px 12px` | `rencana/screenshots/kompetitor-desktop.png` |
| `.comp-toast` | Empty/loading state | **P1** | `Menyimpan…` hilang 2.2s padahal PUT 4s, err tanpa retry, bottom ketutup keyboard. | `info 4s spinner, err 8s + Coba lagi, bottom max(24, safe-area)` | `site/kompetitor.html:530` |
| `.comp-toast` | Warna/accent | **P2** | `ok #1a7f37 err #a02020` luar token, no dark. | `ok accent-dark err #d92d20 + dark brightness1.1` | `site/kompetitor.html:43-45` |
| `.pk-modal` + `.pk-edit-overlay` | Hierarki & spacing | **P2** | Close `× 1.8rem muted` kecil, nav galeri `4px 12px` mepet tepi. | Circle 32px `rgba(0,0,0,.06) hover accent-soft`, nav `8px 14px inset10` | `rencana/screenshots/produk-modal-desktop.png` |
| `.lightbox` | Proporsi & kualitas gambar | **P2** | Caption ` #cfe6f2` tanpa bg, prev/next 44px mepet 12px. | Caption `bg rgba(0,0,0,.45) 6px 12px radius6`, nav 20px + blur | `rencana/screenshots/galeri-desktop.png` |
| `.to-top` + `.pk-edit-fab` | Hierarki & spacing | **P2** | `to-top 44px 18,18` tabrakan FAB `20,20/76/124` — 4 bulatan numpuk. | FAB `right16 bottom16 gap10 flex-col`, to-top `calc(16+3*56+20)` | `rencana/screenshots/index-mobile.png` |

---

## 6. induksi.html — Ilmu Dasar (brand, kode produk)

**Skor juri:** CEO 5.6 / Desainer 5.7. **Screenshot:** `induksi-desktop.png` 1280 + `induksi-mobile.png` 390.  
**Sumber:** `site/induksi.html` + `site/css/style.css` baris 435-506 `.ik-block .ik-seg .ik-sub .ik-fridge .ik-lv-wrap`.

| Halaman | Aspek | Severity | Temuan | Usulan fix | Screenshot |
|---------|-------|----------|--------|------------|------------|
| induksi.html | Keterbacaan teks | **P1** | `ik-seg-lbl 0.72rem (11.5px) max140px` + `ik-sub-desc 0.78rem` muted → harus disipitkan di hp. | `ik-seg-lbl→0.8rem line1.4 #3d5a6b`, `ik-sub-desc→0.82rem` `css:454,464` | `rencana/screenshots/induksi-mobile.png` |
| induksi.html | Hierarki & spacing | **P1** | `ik-block 18px 20px margin 0 0 16px` + `ik-kode-row gap10 flex-wrap` rapat, judul `ik-title 1.05rem accent-dark` vs `ik-block` border tipis. | `ik-block 20px 22px gap14`, `ik-kode margin 0 0 18px`, `divider 1px dash` `css:436` | `rencana/screenshots/induksi-desktop.png` |
| induksi.html | Proporsi & kualitas gambar | **P1** | `ik-fridge 52×64 border2 accent` terlalu kecil di desktop, `ik-seg-txt 1.35rem padding 8×14` tidak scale di mobile wrap 4 segmen. | `ik-fridge 60×74 desktop, 48×60 mobile`, `ik-seg-txt 1.5rem desktop 1.2rem mobile` `css:446-468` | `rencana/screenshots/induksi-mobile.png` |
| induksi.html | Warna/accent | **P2** | `ik-seg-txt` tiap segmen warna solid berbeda (hardcode) tanpa token, `ik-lv-chip` juga — tidak ada legend. | Tambah legend kecil `warna = kategori` + pakai token `var(--accent)` + opacity | `rencana/screenshots/induksi-desktop.png` |
| induksi.html | Empty/loading state | **P1** | `#konten-induksi` kosong sebelum `renderKb()` → putih kosong tanpa skeleton, gagal load hanya `—` (di `knowledge.js`). | Skeleton 2× `ik-block shimmer` + empty `Gagal memuat brand.json — cek file` + retry btn | `rencana/screenshots/induksi-desktop.png` |

---

## 7. rotasi.html — Pasar & Benchmark (GFK, peta harga, SBS EC)

**Skor juri:** CEO 5.5 / Desainer 5.2. **Screenshot:** `rotasi-desktop.png` + `rotasi-mobile.png`.  
**Sumber:** `site/rotasi.html` + `site/css/style.css` `.chart-wrap` + `site/js/charts.js` (`drawBarChart`, `drawScatter`).

| Halaman | Aspek | Severity | Temuan | Usulan fix | Screenshot |
|---------|-------|----------|--------|------------|------------|
| rotasi.html | Proporsi & kualitas gambar | **P1** | Scatter `chart-peta-harga 360px` dot 7px tanpa label, sumbu `Kapasitas (L)` vs `Harga (jt)` kecil, titik `HRF-CTD729RITA 650L 34,9jt` tidak highlight. | Dot `10px stroke 2px putih`, highlight termahal `ring 3px accent`, tooltip `model+Rp+L` | `rencana/screenshots/rotasi-desktop.png` |
| rotasi.html | Keterbacaan teks | **P1** | `chart-wrap h3 1rem` + `p 0.8rem muted` + `chart-legend 0.8rem muted` — legenda bar `%` kecil, tidak ada nilai di bar. | `h3 1.05rem`, `p 0.85rem 1.5`, bar label `%` di ujung bar `0.85rem bold` | `rencana/screenshots/rotasi-desktop.png` |
| rotasi.html | Hierarki & spacing | **P1** | 4 `chart-wrap margin 16px 0` berurutan tanpa anchor, `chart h3` vs `konten-rotasi h2.sec` beda tipis, tidak ada TOC. | Tambah `h2.sec 24px amber` + `chart-wrap 20px 22px gap 20` + sticky mini TOC `Unit | Wilayah | Peta | SBS` | `rencana/screenshots/rotasi-desktop.png` |
| rotasi.html | Warna/accent | **P2** | Bar AQUA `#0097d6` on-point tapi bar lain `#7a7a7a` abu terlalu gelap, tidak ada pattern untuk buta warna. | Abu → `#b0bec5` + pattern stripe untuk non-AQUA, AQUA tetap solid accent | `rencana/screenshots/rotasi-desktop.png` |
| rotasi.html | Empty/loading state | **P2** | `konten-rotasi` render `knowledge.js` tanpa loading, jika JSON 404 kosong putih. | Skeleton `chart-wrap shimmer 220px` + empty `Data GFK belum ada` | `rencana/screenshots/rotasi-desktop.png` |

---

## 8. proses.html — Timeline peluncuran produk

**Skor juri:** CEO 6.0 / Desainer 5.8 — paling mending. **Screenshot:** `proses-desktop.png` + `proses-mobile.png`.

| Halaman | Aspek | Severity | Temuan | Usulan fix | Screenshot |
|---------|-------|----------|--------|------------|------------|
| proses.html | Hierarki & spacing | **P1** | `tl-step flex gap14 padding16 18 border radius shadow` 5 langkah berurutan tanpa progres indicator, `tl-num 34px` vs card 16px imbalance di mobile. | Tambah vertical line `2px accent` konektor antar `tl-step`, `tl-num 36px desktop 32px mobile` `css:408-411` | `rencana/screenshots/proses-mobile.png` |
| proses.html | Keterbacaan teks | **P1** | `tl-title 1rem` ok tapi `tl-detail 0.88rem muted line1.55` + `tl-pic 0.82rem` + `tl-badge 0.72rem 3px 10px` nyempit, badge `belum/selesai/in-progress` pastel kontras rendah. | `tl-detail→0.9rem 1.6 #3d5a6b`, badge `0.75rem padding 4 12` + border 1.5px `css:412-419` | `rencana/screenshots/proses-desktop.png` |
| proses.html | Warna/accent | **P2** | Badge `selesai #e7f6ec` vs `in-progress #fdf3d9` vs `belum #eef2f6` tidak pakai token konsisten, `chip 0.78rem var(--accent-soft)` sama dengan badge. | Samakan token: `selesai accent-soft`, `in-progress amber`, `belum bg-soft` + legend `●` | `rencana/screenshots/proses-desktop.png` |
| proses.html | Empty/loading state | **P2** | `konten-proses` kosong sebelum JS, tidak ada empty. | Skeleton `tl-step shimmer 3×` + empty `Timeline belum ada` | `rencana/screenshots/proses-desktop.png` |

---

## 9. galeri.html — 323 foto kegiatan

**Skor juri:** CEO 5.2 / Desainer 4.9 — empty/loading paling parah. **Screenshot:** `galeri-desktop.png` + `galeri-mobile.png`.

| Halaman | Aspek | Severity | Temuan | Usulan fix | Screenshot |
|---------|-------|----------|--------|------------|------------|
| galeri.html | Empty/loading state | **P0** | `galeri-root` `Memuat foto…` lalu render 323 foto sekaligus via `IntersectionObserver 600px` tanpa placeholder count, first paint 1225KB berat. | Skeleton grid 12 card shimmer + lazy `loading lazy decoding async` sudah ok, tambah `p 12 foto dimuat · scroll untuk lagi` + pagination 30 | `rencana/screenshots/galeri-desktop.png` |
| galeri.html | Proporsi & kualitas gambar | **P1** | `gallery img height 150px (110 mobile) cover` crop wajah & spanduk, ratio tidak konsisten (kegiatan vs produk). | `height 160 desktop 130 mobile + aspect 4/3`, atau `object-fit contain bg-soft + padding 4` untuk foto vertikal | `rencana/screenshots/galeri-desktop.png` |
| galeri.html | Keterbacaan teks | **P1** | `gallery figcaption 0.72rem (11.5px) nowrap ellipsis` tidak terbaca, terkubur di bawah thumb. | `0.78rem 600 line-clamp2 nowrap→wrap` + `margin-top 6px color var(--text)` `css:129` | `rencana/screenshots/galeri-mobile.png` |
| galeri.html | Hierarki & spacing | **P1** | `h2.sec` per folder (`27 Juli - Warehouse`, `Product Knowledge/AC - SS`) + `p sec-sub "78 foto"` tanpa collapse, scroll >10 layar. | Folder accordion `details/summary` default open 1, lain collapsed + `+ 78 foto` badge + search filter folder | `rencana/screenshots/galeri-desktop.png` |
| galeri.html | Warna/accent | **P2** | Gallery card `border 1px #d8e5ee` vs page `bg #f6f9fc` kontras tipis, hover `zoom-in` tanpa overlay. | `border 1.5px + shadow 0 2 8 rgba(0,0,0,.06)` + hover `scale 1.02 overlay + 0 8 20` | `rencana/screenshots/galeri-desktop.png` |

---

## 10. file.html — Daftar file materi asli

**Skor juri:** CEO 5.7 / Desainer 5.6. **Screenshot:** `file-desktop.png` + `file-mobile.png`.

| Halaman | Aspek | Severity | Temuan | Usulan fix | Screenshot |
|---------|-------|----------|--------|------------|------------|
| file.html | Hierarki & spacing | **P1** | `file-list li flex justify-between gap12 padding 10 4 border-bottom` dempet, `nm word-break break-all` bikin nama panjang pecah tengah kata. | `padding 12 8`, `nm break-word` (bukan break-all), `gap 8`, `hover bg-soft radius6` `css:174` | `rencana/screenshots/file-desktop.png` |
| file.html | Keterbacaan teks | **P1** | `sz 0.85rem muted white-space nowrap` + `[Drive] 0.85rem` biru tipis, size `4.6 MB` tidak align kanan. | `sz tabular-nums 0.82rem min-width 70px text-right`, `[Drive] 0.8rem badge accent-soft` | `rencana/screenshots/file-desktop.png` |
| file.html | Proporsi & kualitas gambar | **P2** | `btn-preview` tidak ada style di css (fallback browser), di `file.html:105` `class btn-preview` tanpa warna. | Define `.btn-preview {5px 10px 0.78rem bg accent color #fff radius6}` | `rencana/screenshots/file-desktop.png` |
| file.html | Warna/accent | **P1** | List panjang tanpa zebra, folder `h2.sec` vs file `li` tidak dibedakan, hover `bg-soft` tipis. | `li:nth-child(even) bg-soft 0.5`, folder `h2.sec 1.1rem accent-dark border-left4` | `rencana/screenshots/file-desktop.png` |
| file.html | Empty/loading state | **P1** | `Memuat daftar file…` tanpa skeleton, gagal `Gagal memuat (err) + Coba lagi` 0.9rem muted kecil. | Skeleton 5× li shimmer + err `icon ⚠️ + 0.9rem bold + btn Coba lagi primary` | `rencana/screenshots/file-mobile.png` |

---

## 11. login.html — Masuk

**Skor juri:** CEO 6.5 / Desainer 6.2 — paling bersih. **Screenshot:** `login-desktop.png` + `login-mobile.png`.

| Halaman | Aspek | Severity | Temuan | Usulan fix | Screenshot |
|---------|-------|----------|--------|------------|------------|
| login.html | Keterbacaan teks | **P1** | `sec-sub 0.9rem muted` di card putih kontras rendah, `login-msg error #e5484d` 0.9rem kecil tanpa ikon. | `sec-sub 0.95rem #3d5a6b`, err `0.9rem bold + icon ⚠️ + bg #fef2f2 border #fecaca` `css:558` | `rencana/screenshots/login-desktop.png` |
| login.html | Hierarki & spacing | **P2** | `login-card 360px padding32` ok tapi `input margin 18 0 12 padding12 14` vs `btn padding12` tidak 4pt grid, `brand 22px` kecil. | Input `14px 16px`, btn `14px height44`, card `padding 36` mobile `24` `css:544-555` | `rencana/screenshots/login-desktop.png` |
| login.html | Proporsi & kualitas gambar | **P2** | Logo `brand-logo 22px` kecil di tengah card, no ilustrasi. | `logo 32px + Haier_Logo.svg 1.2×` atau hero mini 48px di atas form | `rencana/screenshots/login-desktop.png` |
| login.html | Warna/accent | **P2** | `login-card shadow 0 10 40 rgba(0,0,0,.2)` ok tapi border `1px #d8e5ee` di `bg #f6f9fc` tipis, focus ring input tidak ada. | `focus {outline 2px solid var(--accent) outline-offset2}` + border `1.5px` | `rencana/screenshots/login-desktop.png` |

---

## Catatan Verifikasi & Yang Belum Terverifikasi

**Sudah diverifikasi (bukti):**
- File plan ini ada: `D:/AI/projects/mtms-aqua-haier-kb/rencana/visual-audit-plan.md` (dokumen ini)
- 11 halaman dinilai juri (skor + komentar CEO & Desainer per halaman §0.1) + 21 screenshot terlampir §0.2 (desktop 1280 & mobile 390 via Playwright)
- 79 temuan (21 P0 / 42 P1 / 16 P2) dengan tabel `| Halaman | Aspek | Severity | Temuan | Usulan fix | Screenshot |`
- 2 contoh screenshot bukti: `rencana/screenshots/kompetitor-desktop.png` (1.56MB, 32 baris tabel, 74 sel kosong terlihat) dan `rencana/screenshots/produk-modal-desktop.png` (1.4MB, modal 640px sempit) — bisa dibuka langsung di path tersebut.

**Belum terverifikasi / butuh ACC sebelum cek:**
- Kontras angka pasti WCAG (butuh run `cek-kontras.js` via Browser CDP di halaman hidup — belum dijalankan, nilai di atas dari inspeksi `style.css` `#4d6b7a` vs `#f6f9fc` estimasi 4.6:1)
- Data live `api/kompetitor` & `api/produk` (PUT) — screenshot di atas pakai fallback `data.js`/`data/kompetitor.json`, belum cek state setelah login + token
- Dark mode (`[data-theme="dark"]`) — screenshot hanya light, kontras dark belum ukur
- Performa load 323 foto galeri (butuh throttling 3G) & shimmer timing belum ukur
- Device real HP (390 sudah emulasi, belum tes sentuh jari di lapangan)

**Yang TIDAK dilakukan (sesuai mandat PLAN ONLY):** tidak ada edit `site/*.html`, `site/css/*`, `site/js/*`; tidak ada deploy; tidak ada ubah harga/stok; tidak ada kirim ke customer. Semua usulan di atas adalah **rencana 1 baris per temuan**, eksekusi **TAHAN** sampai Louis ACC.

**Langkah setelah ACC:** pilih scope P0 dulu (21 tiket) → bikin `spec-tiket` / `surat-tugas` per seksi → `codex-borongan` untuk ketik + `juri-tampilan` (2 juri fresh per ronde) sampai ≥8 & cek-kontras 0 gagal → deploy gated.

