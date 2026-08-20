# Tiket B — Fix file:// (embed data, hapus ketergantungan fetch)

Bikin situs kebuka sempurna dari folder lokal (file://) tanpa server: semua data JSON
di-embed ke `site\js\data.js` sebagai `window.MTMS_DATA`, renderer baca dari situ
dulu (fallback fetch tetap ada buat jalur http).

```estafet
id: B
status: kelar
depends_on: [A]
owner: subagen-claude-general
verifier: mandor-sesi-utama
file_disentuh:
  - tools\gen_data_js.py
  - tools\verify_file_proto.py
  - site\js\data.js
  - site\js\produk.js
  - site\js\knowledge.js
  - site\js\search.js
  - site\index.html
  - site\induksi.html
  - site\produk.html
  - site\rotasi.html
  - site\proses.html
  - site\galeri.html
  - site\file.html
cek_selesai:
  - "python -X utf8 D:\\AI\\projects\\mtms-aqua-haier-kb\\tools\\verify_file_proto.py -> exit 0, 'errors: 0' dan 'render_gagal: 0' untuk 7 halaman file://"
  - "python -X utf8 D:\\AI\\projects\\mtms-aqua-haier-kb\\tools\\gen_data_js.py -> exit 0 (regenerasi idempoten)"
gerbang_acc:
```

## Detail
1. `tools\gen_data_js.py`: baca `site\data\produk-katalog.json`, `site\data\knowledge\*.json` (12), `site\data\galeri.json`, `site\data\files.json` → tulis `site\js\data.js` berisi `window.MTMS_DATA = {katalog:[...], knowledge:{namafile:{...}}, galeri:[...], files:[...]}`.
2. Ubah 5 konsumen data: `produk.js` (renderKatalog), `knowledge.js` (renderKb), `search.js` (loadKbIndex), inline script `galeri.html`, inline script `file.html` → sumber utama `window.MTMS_DATA`, fallback `fetch()` kalau MTMS_DATA undefined.
3. Semua 7 HTML: `<script src="js/data.js"></script>` SEBELUM renderer lain.
4. `tools\verify_file_proto.py`: Playwright buka `file:///D:/AI/projects/mtms-aqua-haier-kb/site/<hal>.html` ×7 (390 & 1280), cek konten render (kartu/foto/daftar > 0), 0 console error, print `errors: N` + `render_gagal: N`.
5. CATATAN: `site\media\` = mirror, JANGAN sentuh. Aset baru selalu ke `site\assets\`.
