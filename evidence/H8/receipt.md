tiket: H8
status: selesai
ringkasan:
  model: mandor + vision free (dots-3-note-preview:free via opencode run --agent pekerja-flash)
  QC visual final + laporan: screenshot 10 (desktop+mobile: produk/induksi/proses/file/modal) -> nilai model vision -> temuan P0/P1/P2 -> MANDOR verifikasi ulang di DOM asli (nol percaya vision). Semua P0/P1 vision terbukti FALSE ALARM (boundary screenshot viewport 800px; modal & halaman sebenarnya scrollable, tabel tidak meluber). Sisa asli = kosmetik minor. Laporan bab baru di LAPORAN-2026-08-18-MTMS.md, papan rencana\09-rombak-h4-h8.md + _ESTAFET.md diupdate.
artifacts:
  - evidence\H8\screens\ (10 png)
  - evidence\H8\qc-visual.md (skor + vonis mandor per temuan)
  - evidence\H4..H8\receipt.md + evidence\H6\receipt-kerja.md + evidence\H5\produk-katalog.before-h5.json + evidence\H6\produk-katalog.before.json
  - LAPORAN-2026-08-18-MTMS.md (bab H4-H8)
bukti:
  - opencode run dots-3-note-preview:free -> laporan QC (10 skor, 2 P0, 3 P1, 2 P2)
  - Playwright mandor modal mobile: scrollHeight 1204 > clientHeight 715 (scrollable), garansi visible setelah scroll true
  - Playwright mandor tabel ringkasan mobile: docHScroll false, tableScrollW==tableClientW 320
  - verify_file_proto.py exit 0; LIVE 45 kartu 0 err
unknowns:
  - Vision model gratis tak selalu bisa baca gambar (nemotron-3-nano-omni bilang "TIDAK BISA"); dots-3 andal.
  - P0/P1 vision diturunkan ke minor setelah verifikasi mandor; kalau mau 100% yakin tampilan mobile penuh, buka di HP asli.
