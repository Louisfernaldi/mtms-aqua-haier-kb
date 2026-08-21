# Bukti Sensus Taksonomi Spesifikasi

Tanggal: 2026-08-21 WIB

## Korpus Lokal

- `site/data/kompetitor.json`: 102 model unik, 6 merek, 456 bullet fitur.
- Merek: AQUA 32, LG 16, MIDEA 7, POLYTRON 13, SAMSUNG 11, SHARP 23.
- `site/data/produk-katalog.json`: 42 model AQUA; gross 42/42, nett 37/42, material 36/42, daya 32/42, garansi 37/42.
- `capacity_l` lama tidak aman dianggap nett: 16 dari 32 model AQUA overlap tidak sama dengan gross maupun nett katalog.

## Sumber Resmi Sampel

- AQUA: https://aquaelektronik.com/product/63/DOUBLE+DOOR+TOP+MOUNT
- LG: https://www.lg.com/id/kulkas-dan-freezer/bottom-freezer/gn-v389fqef/
- Midea: https://www.midea.com/id/refrigerators/fridge/2-door
- Polytron: https://polytron.co.id/produk/polytron-kulkas-2-pintu-flexup-5in1-prw-29hb/
- Samsung: https://www.samsung.com/id/refrigerators/top-mount-freezer/rt6300c-top-mount-freezer-optimal-fresh-and-space-max-393l-black-rt38cg6420b1se/
- Sharp: https://id.sharp/products/home-appliances/sj-246gi-gk-2-door-shine-glassdoor-j-tech-inverter

## Dua Belas Kategori Inti

| Urutan | Key | Label | Grup | Unit | Tipe |
|---:|---|---|---|---|---|
| 10 | `form_factor` | Tipe Kulkas | Konfigurasi | - | enum |
| 20 | `door_count` | Jumlah Pintu | Konfigurasi | pintu | integer |
| 30 | `freezer_position` | Posisi Freezer | Konfigurasi | - | enum |
| 40 | `gross_capacity_l` | Kapasitas Kotor | Kapasitas | L | number |
| 50 | `net_capacity_l` | Kapasitas Bersih | Kapasitas | L | number |
| 60 | `width_mm` | Lebar | Dimensi | mm | number |
| 70 | `height_mm` | Tinggi | Dimensi | mm | number |
| 80 | `depth_mm` | Kedalaman | Dimensi | mm | number |
| 90 | `rated_power_w` | Daya Listrik | Performa | W | number |
| 100 | `compressor_type` | Jenis Kompresor | Performa | - | enum |
| 110 | `cooling_system` | Sistem Pendinginan | Performa | - | enum |
| 120 | `defrost_type` | Sistem Defrost | Performa | - | enum |

Semua kategori aktif dan tampil di tabel utama. Nilai kosong berarti belum ditemukan, bukan berarti fitur tidak ada.

## Aturan Normalisasi

- Identitas model harus exact `brand + model`; alias perlu daftar eksplisit, bukan fuzzy match.
- Kapasitas gross, nett, kulkas, dan freezer tidak boleh dicampur.
- Watt daya terukur tidak sama dengan konsumsi tahunan atau klaim hemat persen.
- `null` berarti belum diketahui; `false` hanya jika sumber menyatakan fitur tidak ada.
- Nama teknologi merek tetap bullet asli. Tag kemampuan global hanya ditambahkan bila maknanya eksplisit.
- Nilai user tidak pernah ditimpa riset; konflik baru menjadi suggestion.

## Kategori Opsional

Garansi unit/kompresor, material/warna, refrigeran, berat, kapasitas kompartemen, konsumsi tahunan, noise, climate class, ice maker, dispenser, alarm pintu, Wi-Fi/app, convertible zone, humidity control, deodorizer, antibacterial, shelf, display, dan tahun rilis.
