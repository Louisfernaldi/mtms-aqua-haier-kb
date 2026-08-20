tiket: H4
status: selesai
ringkasan:
  model: sesi-utama (mandor opencode) + subagen-general
  Pasang foto untuk 14 model baru + model lama yang punya file. Mekanisme: gen_data_js.py sudah membangun foto_list otomatis dari scan site\assets\produk (prefix MODEL__, urut __0,__1,...,__web0 terakhir) — setelah rombakan model H6/H7 (nol label "/"), data.js diregen dan SEMUA kartu yang filenya ada dapat foto_list. 14 model baru lengkap: CTD506RGC/GG 4 foto, 405IG 1, 355IG/IM 2, DTM305/285/265RAV 2, DTM305/285/265RAP 1, DTM285/265/245CBP 1. Field foto lama tidak hilang (produk.js pakai p.foto || p.foto_list[0]).
artifacts:
  - site\js\data.js (diregen, 45 katalog, foto_list terisi otomatis)
  - tools\gen_data_js.py (tidak diubah — sudah benar)
  - tools\verify_file_proto.py (ambang pk-card 51 -> 45, update di H6)
bukti:
  - gen_data_js.py -> "data.js ditulis OK (45 katalog, ...)"
  - cek basename: 0 item foto_list yang prefix-nya salah ("<model>__")
  - kartu dengan foto_list >= 1: 38 dari 45 (sebelum rombakan 37 dari 51)
  - Playwright file:// produk.html: 45 pk-card, klik AQR-CTD506RGC -> modal open, 4 pk-gal-thumb; AQR-CTD506RGG -> 4 thumbs; 0 console error desktop+mobile, 0 h-scroll
  - verify_file_proto.py -> exit 0 (errors: 0, render_gagal: 0)
  - LIVE https://master.mtms-aqua-haier-kb.pages.dev/produk.html (deploy 4d121a0a): 45 kartu, 38 img load 0 fail, 0 console error, 0 h-scroll
unknowns:
  - 7 kartu TETAP tanpa foto (nol file di assets\produk): AQR-320RBG, AQR-CTD506RBG, AQR-CTD506RBC, AQR-TSE696RAV, AQR-DTM248CBP, AQR-DTM268CBP, AQR-DTM288CBP. Alasan: file foto tidak ada di folder (tidak difabrikasi).
