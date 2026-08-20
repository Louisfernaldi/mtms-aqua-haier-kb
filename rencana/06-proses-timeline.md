# Tiket E — Rombak proses.html: teks padat → timeline visual

8 kartu paragraf panjang → timeline bernomor untuk alur launch T588 + kartu latihan
Excel ber-bullet. Readability naik drastis di mobile.

```estafet
id: E
status: kelar
depends_on: [D]
owner: subagen-claude-general
verifier: mandor-sesi-utama
file_disentuh:
  - site\data\knowledge\proses.json
  - site\data\knowledge\tugas.json
  - site\js\proses.js
  - site\proses.html
  - site\css\style.css
  - tools\verify_proses.py
  - tools\gen_data_js.py
  - site\js\data.js
cek_selesai:
  - "python -X utf8 D:\\AI\\projects\\mtms-aqua-haier-kb\\tools\\verify_proses.py -> exit 0: '.tl-step' >= 8, paragraf > 320 karakter di #konten-proses == 0, 0 console error"
gerbang_acc:
```

## Detail
- Rombak `proses.json` → struktur baru khusus timeline (field `langkah: [{urut, judul, pic, status, detail}]` dari fakta "Tahapan New Product Launch" 8 langkah: price list Hendry 3 Agu, display plan Sherline 6 Agu, POP design in-progress, sellout program, sell-in plan, training Lidia 6 Agu, internal meeting Sapto 7 Agu, PSI stok) — field `fakta` LAMA dipertahankan supaya renderKb/search halaman lain tetap aman.
- `site\js\proses.js` (baru): render (1) timeline vertikal bernomor lingkaran (nomor + judul pendek + PIC + status badge berwarna: selesai=hijau, in progress=kuning, belum=abu) + detail 1-2 baris, (2) section "Kunci sukses" 1 kartu pendek, (3) tugas.json → kartu latihan Excel per soal: judul + bullet poin (angka penting jadi badge/chip: Rp10.000/jam, 5% pajak, dst), BUKAN paragraf.
- Line-height longgar, whitespace cukup, mobile-first (390px) — cek h-scroll.
- proses.html: ganti renderKb jadi proses.js (renderTugas + renderTimeline), tetap include knowledge.js/search.js.
