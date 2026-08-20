tiket: H5
status: selesai (sebagian field tetap null karena sumber tak ada)
ringkasan:
  model: sesi-utama (mandor) + subagen-general (riset web)
  Lengkapi spek null 14 model baru + model lama. Subagen riset 16 model dari halaman resmi aquaelektronik.com (source_url dari AQUA.json) + master.json + produk-katalog.json; output riset-spek-h5.json. MANDOR verifikasi & terapkan hanya nilai bersumber: (1) varian/flags/serie CTD506RGC (CB/Inverter/Magic Zone) & CTD506RGG (BK/Inverter/Magic Zone) dari halaman resmi + master.json; (2) 405IG & 355IG: material Kaca (Glass) [fitur Glass Door resmi], garansi 12 [alt-text resmi], varian BK, flags Inverter; 355IM: garansi 12, varian BB, flags Inverter; (3) kapasitas_nett CBP dari master.json: DTM245CBP 185, DTM265CBP 205, DTM285CBP 225 (konsisten keluarga DTM248/268/288).
artifacts:
  - D:\AI\tmp\win-temp\opencode\riset-spek-h5.json (hasil riset 16 model, tiap nilai + sumber)
  - site\data\produk-katalog.json (8 kartu diisi; backup evidence\H5\produk-katalog.before-h5.json)
bukti:
  - produk-katalog.json: 45 kartu, field konsisten (JSON valid), verifikasi diff 8 kartu berubah sesuai tabel di atas
  - gen_data_js.py -> data.js ditulis OK (45)
  - verify_file_proto.py -> exit 0
  - sumber per nilai tercantum di riset-spek-h5.json (URL aquaelektronik.com + master.json path)
unknowns:
  - daya_watt TETAP null untuk 7 model: CTD506RGC, CTD506RGG, 405IG, 355IG, 355IM, DTM245/265/285CBP (spek resmi AQUA berupa GAMBAR di halaman web, tak ada sumber teks; 2 sumber gagal -> null + catat). Juga TSE605RBM & TSE696RAV daya null (belum ada sumber).
  - kapasitas_nett CTD506RGC/RGG TIDAK diisi: sumber bentrok (AQUA gross 401/406 vs master nett 406 untuk keduanya; nett>gross mustahil) -> ditunda jujur.
  - Serie RAP/RAV & CBP tetap null (tak ada sumber teks resmi).
