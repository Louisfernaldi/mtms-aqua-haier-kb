tiket: H7
status: selesai
ringkasan:
  model: subagen-general (eksekusi) + mandor (verifikasi)
  Bersihkan kartu dobel varian tanpa foto: AQR-DTM248CBP, AQR-DTM268CBP, AQR-DTM288CBP tampil 2x (grup varian PE/ME/BE = Chic Color vs DS/LS/SB/SG = Magic Neo). Data identik (kapasitas, daya, material, garansi, flags, benefit) -> GABUNG jadi 1 kartu per model: varian ["PE","ME","BE","DS","LS","SB","SG"], serie "Chic Color / Magic Neo", harga tetap null (tak ada sumber). Jumlah kartu turun 51 -> 48 pada langkah ini (45 setelah H6).
artifacts:
  - site\data\produk-katalog.json (6 kartu -> 3 kartu)
  - backup: evidence\H6\produk-katalog.before.json (sebelum rombakan H6+H7)
bukti:
  - AQR-DTM248CBP cuma 1 kartu dgn varian 7 item; DTM268CBP 1 kartu; DTM288CBP 1 kartu (cek mandor)
  - JSON valid, 45 kartu final, verify_file_proto.py exit 0
  - produk.html render (file:// + LIVE) 45 kartu, 0 console error
unknowns:
  - Pola dobel varian yang SAMA juga ada di AQR-D185/D205/D225 (Chic Color vs Magic Neo, tapi punya foto + harga) — DI LUAR lingkup tiket (tiket ini khusus "tanpa foto"), dicatat sebagai temuan, direkomendasikan digabung, nunggu keputusan Louis (lihat LAPORAN).
