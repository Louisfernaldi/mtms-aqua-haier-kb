# Tiket F — Rombak "Ringkasan Pengetahuan" jadi Visual

13 kartu teks paragraf di produk.html → jadi blok visual: tabel segmen harga + kartu angka.
Data sama (produk-kulkas.json + produk-katalog.json), bentuk beda.

```estafet
id: F
status: kelar
depends_on: [C]
owner: subagen-claude-general
verifier: mandor-sesi-utama
file_disentuh:
  - site\produk.html
  - site\js\produk.js
  - site\css\style.css
  - site\data\knowledge\produk-kulkas.json
  - tools\verify_ringkasan.py
  - tools\gen_data_js.py
  - site\js\data.js
cek_selesai:
  - "python -X utf8 D:\\AI\\projects\\mtms-aqua-haier-kb\\tools\\verify_ringkasan.py -> exit 0: '#ringkasan-visual table tbody tr' >= 5, '.stat-card' >= 4, 0 console error"
gerbang_acc:
```

## Detail
- Ganti section `Ringkasan Pengetahuan` (id=konten-produk, renderKb 13 kartu paragraf) jadi section `<section id="ringkasan-visual">` berisi:
  1. **Tabel segmen harga**: baris = segmen (Single Door/2 Pintu TM/BM/SBS/Multidoor), kolom = rentang harga (dari fakta "Rentang harga per segmen" produk-kulkas.json) + jumlah model + kapasitas range (hitung dari produk-katalog.json, MESIN bukan tangan).
  2. **Kartu angka (stat-card)**: garansi kompresor terpanjang (th), daya terhemat (W), jumlah model, jumlah varian — dihitung dari katalog JSON.
  3. Fakta teks sisanya (seri, analisa segmen) → maksimal 3-4 kartu pendek bullet, BUKAN paragraf >3 baris.
- Rombak boleh ubah struktur `produk-kulkas.json` (tambah blok terstruktur `segmen_harga: [...]`) selama renderKb halaman lain tetap aman (field `fakta` dipertahankan).
- Angka WAJIB hasil hitung script dari JSON, sumber ditandai.
