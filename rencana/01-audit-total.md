# Tiket A — Audit Total 7 Halaman (read-only, subagen paralel)

Audit konten + tampilan + data per halaman LIVE, output daftar temuan terprioritisasi.
TIDAK mengubah satu pun berkas situs. 3 subagen paralel menulis berkas temuan terpisah,
mandor menjahitnya jadi 1 laporan audit via kode.

```estafet
id: A
status: kelar
depends_on: []
owner: subagen-audit-paralel
verifier: mandor-sesi-utama
file_disentuh:
  - tools\audit\A1-index-induksi.md
  - tools\audit\A2-produk-proses.md
  - tools\audit\A3-rotasi-galeri-file.md
  - tools\audit-total-20260818.md
cek_selesai:
  - "Test-Path D:\\AI\\projects\\mtms-aqua-haier-kb\\tools\\audit-total-20260818.md -> True"
  - "(Select-String -Path tools\\audit-total-20260818.md -Pattern '^## ').Count -> >= 7"
gerbang_acc:
```

## Detail
- Target live: https://master.mtms-aqua-haier-kb.pages.dev (7 halaman: index, induksi, produk, rotasi, proses, galeri, file).
- Metode: Playwright headless 1280x800 + 390x844 (Chrome `C:\Program Files\Google\Chrome\Application\chrome.exe`), hitung konten nyata (jumlah kartu/img/tabel/jumlah kata), console error, h-scroll, img pecah, alt kosong; bandingkan source lokal `site\*` vs materi `tools\extracted\*.txt` (LEWATI file >5MB — pakai nama + head saja).
- Fokus temuan: (a) section polos/tanpa visual, (b) teks padat >4 baris tanpa bullet, (c) data materi bagus belum masuk situs, (d) inkonsistensi antar halaman.
- Prioritas P1/P2/P3 per temuan + angka bukti.
