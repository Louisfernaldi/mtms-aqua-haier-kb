# QC Visual H8 — MTMS AQUA Knowledge Hub (rombakan katalog 45 kartu)

**Waktu**: 18 Agu 2026 ~22:10-23:00 WIB
**Model vision**: `openrouter/dots-studio/dots-3-note-preview:free` (vision-capable, terbukti bisa baca gambar; `nemotron-3-nano-omni-30b` tidak bisa lihat gambar)
**Screenshot**: `evidence\H8\screens\` (10 file: produk/induksi/proses/file/modal × desktop 1280×800 + mobile 390×844)

## Skor per halaman (vision)
| File | Skor | File | Skor |
|---|---|---|---|
| file_desktop | 9 | file_mobile | 8 |
| induksi_desktop | 9 | induksi_mobile | 8 |
| modal_ctd506rgc_desktop | 8 | modal_ctd506rgc_mobile | 7 |
| produk_desktop | 9 | produk_mobile | 7 |
| proses_desktop | 9 | proses_mobile | 8 |

## Temuan vision → VONIS MANDOR (diverifikasi di DOM asli, bukan cuma screenshot)
| Temuan | Vonis | Bukti mandor |
|---|---|---|
| P0-1 modal mobile tabel terpotong (garansi tak terbaca) | **FALSE ALARM** | `.pk-modal-box` punya `max-height:85vh; overflow-y:auto`; Playwright mobile: scrollHeight 1204 > clientHeight 715, setelah scroll baris "Garansi kompresor" tampak (true). Vision melihat boundary screenshot (full_page=false viewport 800px). |
| P0-2 modal desktop bawah terpotong | **FALSE ALARM** | sama — modal scrollable via overflow-y auto |
| P1-1 produk_mobile tabel "Segmen & Harga" butuh h-scroll | **FALSE ALARM** | Playwright mobile: docHScroll false, tableScrollW 320 == tableClientW 320 (nol meluber) |
| P1-3 induksi kartu bawah terpotong | **FALSE ALARM** | boundary screenshot (viewport 800px); verify_file_proto render OK desktop+mobile |
| P1-2 file_mobile nav tab wrap 2 baris | **ASLI (minor)** | nav menu mobile wrap — kosmetik, tidak menghalangi, dari H1-H3 |
| P2 (spacing file list, badge NEW menimpa thumb) | **ASLI (minor)** | kosmetik, tidak menghalangi |

## Verifikasi mesin pelengkap
- verify_file_proto.py: exit 0 (errors 0, hscroll 0, render_gagal 0) — 7 halaman × 2 viewport
- Playwright LIVE master.mtms-aqua-haier-kb.pages.dev/produk.html: 45 kartu, 38 img load 0 fail, 0 console error, 0 h-scroll

## Kesimpulan
**0 P0 asli, 0 P1 asli.** Semua temuan kritis dari vision ternyata artefak boundary screenshot (halaman/modal panjang dipotong viewport 800px saat screenshot, padahal bisa discroll). Sisa temuan nyata cuma kosmetik minor (nav wrap mobile, spacing). **LAYAK TAYANG** — tidak ada perbaikan wajib dari gelombang ini.
