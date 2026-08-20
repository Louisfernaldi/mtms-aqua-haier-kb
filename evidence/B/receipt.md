tiket: B
status: lulus
ringkasan:
model: opencode-go/deepseek-v4-flash (mandor koreksi: override -m, zen free kena rate-limit; brief menulis deepseek-v4-flash-free tapi model asli yang jalan go-flash)
Tiket B (Fix file://, embed data ke window.MTMS_DATA) selesai: gen_data_js.py
membangkitkan site\js\data.js (37 katalog, 12 knowledge, 7 galeri, 5 files);
5 konsumen data (produk.js, knowledge.js, search.js, inline galeri.html, inline
file.html) baca window.MTMS_DATA dulu dengan fallback fetch utuh; 7 HTML diberi
<script src="js/data.js"> sebelum renderer; verify_file_proto.py file:// 7 halaman
x 2 viewport = 14 kombinasi, errors: 0, render_gagal: 0, exit 0. Kedua cek_selesai hijau.
next_actions:
- Tidak ada wajib. Opsional: cek cepat halaman via http (server lokal) untuk
  memastikan jalur fallback fetch tetap jalan; bersihkan D:\AI\tmp\win-temp\opencode\cek_datajs.py
  (alat cek sementara, di luar repo).
artifacts:
- tools\gen_data_js.py (baru) - generator embed data -> site\js\data.js
- tools\verify_file_proto.py (baru) - verifier file:// Playwright 7 halaman x 2 viewport
- site\js\data.js (dibangkitkan) - window.MTMS_DATA {katalog, knowledge, galeri, files}
- site\js\produk.js - renderKatalog baca MTMS_DATA.katalog dulu, fallback fetch
- site\js\knowledge.js - renderKb baca MTMS_DATA.knowledge[namafile] dulu, fallback fetch
- site\js\search.js - loadKbIndex iterasi KB_FILES dari MTMS_DATA.knowledge dulu, fallback fetch
- site\index.html, induksi.html, produk.html, rotasi.html, proses.html, galeri.html, file.html
  - masing-masing disisipi <script src="js/data.js"></script> sebelum renderer;
  - galeri.html & file.html: inline renderer baca MTMS_DATA.galeri / MTMS_DATA.files dulu
bukti:
- python -X utf8 tools\gen_data_js.py -> "data.js ditulis OK (37 katalog, 12 knowledge, 7 galeri, 5 files)", exit 0
- python -X utf8 tools\gen_data_js.py (run ke-2) -> "data.js sudah sama, tidak ditulis ulang (idempoten)", exit 0
- python -X utf8 tools\verify_file_proto.py -> 14 baris [OK] (7 halaman x 1280x800 + 390x844),
  tiap baris errs=0 hscroll=false render=True; penutup "errors: 0", "hscroll: 0", "render_gagal: 0"; EXIT=0
- cek payload data.js (script bantu): parsed katalog:37 knowledge:12 galeri:7 files:5,
  "</" tidak ada (escape aman untuk tag script)
unknowns:
- Nol. Catatan kecil (bukan hambatan): verify_file_proto.py mencetak hscroll: 0 hanya
  sebagai informasi — gerbang exit tetap errors + render_gagal sesuai tiket.