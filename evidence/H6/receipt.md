tiket: H6
status: selesai
ringkasan:
  model: subagen-general (eksekusi) + mandor (verifikasi)
  Pecah 3 kartu gabungan berlabel "/" (AQR-DTM265RAP/RAV, AQR-DTM285RAP/RAV, AQR-DTM305RAP/RAV) jadi kartu individual. Data memungkinkan (harga resmi RAP vs RAV BEDA): 6 kartu individual diisi lengkap dari data kartu gabungan + AQUA.json (harga RAP 3860000/4034000/4736000 vs RAV 3975000/4155000/4878000, varian FB vs MX, kapasitas gross/nett 265/205, 285/225, 305/245, range 250-300/250-300/300-350, daya 33.8/33.8/33.5, material Metal, garansi 12, benefit verbatim kartu gabungan). Foto otomatis per model (RAP __web0, RAV __0+__web0).
artifacts:
  - site\data\produk-katalog.json (3 kartu dihapus, 6 kartu diperbaiki; backup evidence\H6\produk-katalog.before.json)
  - evidence\H6\receipt-kerja.md (catatan subagen)
  - tools\verify_file_proto.py (ambang pk-card 51 -> 45)
bukti:
  - produk-katalog.json: 45 kartu, nol model berisi "/", JSON valid exit 0
  - 36 kartu tak tersentuh identik byte-level vs backup (nol regresi) [laporan subagen, dicek mandor via diff hash backup-final]
  - harga RAP vs RAV tampil beda di UI (LIVE: AQR-DTM265RAP Rp 3.860.000)
  - verify_file_proto.py -> exit 0; PLAYWRIGHT produk.html 45 kartu 0 err
unknowns:
  - Hanya 42 model unik dari 45 kartu karena AQR-D185/D205/D225 masing-masing masih 2 kartu (Chic Color vs Magic Neo) — pola dobel varian SAMA seperti CBP H7 tapi di luar lingkup tiket ini; dicatat sebagai temuan/usulan (lihat LAPORAN).
