# Progres Tiket 01 - Fondasi Skema Spesifikasi Dinamis

## 2026-08-21 WIB - STOP karena kontrak kategori inti belum tersedia

Status: **blocked; tidak ada implementasi parsial**.

### Temuan konkret

- `site/data/komparasi_master.json` tidak ada di repo ini. `tools/gen_kompetitor.py` juga menunjuk `MASTER_SRC` ke proyek terpisah, yang berada di luar wilayah tiket.
- `SPEC-fitur-perbandingan-dinamis-v1.md` menetapkan bentuk field kategori, tetapi tidak mencantumkan nama/key 12 kategori inti. SPEC justru menyatakan bahwa 12 kategori inti ditetapkan setelah sensus sumber.
- `03-riset-spesifikasi-semua-model.md` secara eksplisit menempatkan "sensus 102 model" dan "tetapkan 12 kategori inti dari data nyata" di tiket 03. Pada saat yang sama, tiket 03 bergantung pada tiket 01, sedangkan tiket 01 mensyaratkan `spec-categories.json` sudah berisi 12 kategori inti. Ini konflik urutan/dependensi yang mendasar.
- `site/data/kompetitor.json` berisi tepat 102 pasangan brand+model unik dari 6 merek (AQUA 32, LG 16, MIDEA 7, POLYTRON 13, SAMSUNG 11, SHARP 23), tetapi semua model hanya memiliki field lama `capacity_l`, `cat`, `door`, `fitur`, `image`, `model`, `photo_url`, `price_idr`, `price_source`, `source_url`, dan `subcat`. Tidak ada daftar 12 kategori spesifikasi global.
- `site/data/produk-katalog.json` berisi katalog AQUA, dengan beberapa calon field spesifikasi seperti kapasitas, daya, garansi, dan material. Field-field ini tidak cukup untuk menetapkan 12 kategori global bagi 102 model/6 merek tanpa menebak nama, unit, kelompok, urutan, dan status `comparison`.
- Pencarian repo untuk `12 kategori`, `dua belas kategori`, `spec_categories`, `kategori inti`, `research_suggestions`, dan field skema terkait tidak menemukan sumber repo lain yang mencantumkan 12 kategori inti secara eksplisit.

### Alasan berhenti

Membuat `site/data/spec-categories.json` atau pemetaan migrasi sekarang akan mengarang keputusan kategori yang menurut SPEC harus berasal dari sensus tiket 03. Aturan BERHENTI pada tiket aktif melarang tebakan kategori/spesifikasi ketika konflik skema mendasar ini terjadi.

### Yang diperlukan untuk membuka blokir

Sediakan satu sumber repo yang sah dan eksplisit berisi 12 kategori inti lengkap (`key`, `label`, `group`, `unit`, `comparison`, `order`, `active`), atau revisi urutan tiket agar sensus/penetapan kategori dilakukan sebelum migrasi tiket 01. Setelah itu tiket 01 dapat diulang dari kondisi data saat ini.

## 2026-08-21 WIB - Blocker Dibuka

- Sensus lokal 102 model dan riset sampel halaman resmi enam merek selesai.
- Dua belas kategori inti dibekukan di `SPEC-fitur-perbandingan-dinamis-v1.md`.
- Bukti dan aturan normalisasi disimpan di `evidence/taxonomy-research-2026-08-21.md`.
- Tiket 01 boleh diulang tanpa menebak kategori.

### Kondisi berkas

- Tidak dibuat: `site/data/spec-categories.json`, migrator, validator, atau unittest.
- Tidak diubah: `site/data/kompetitor.json`, `site/data/produk-katalog.json`, generator, UI/API, dan sumber di luar workspace.
- Gerbang eksternal tidak dijalankan dan tidak disentuh, sesuai instruksi tiket.

## 2026-08-21 WIB - Implementasi Tiket 01 Selesai

Status: **complete lokal/offline; tidak ada deploy, push, atau tulis-live**.

### Hasil

- `site/data/spec-categories.json` berisi exact 12 kategori inti dari SPEC/evidence, order 10..120, seluruh core `active=true` dan `comparison=true`.
- `tools/migrate_dynamic_specs.py` mengekspor `migrate_document(data, categories)`, menjaga field lama, membuat `model_id` exact `brand::model`, 12 `spec_values` ber-provenance, dan `research_suggestions[]` pada 102 model/6 merek.
- `capacity_l` lama tidak ditebak menjadi gross/nett. Hanya `form_factor` yang diisi dari pemetaan `cat` lama yang eksplisit; core tanpa sumber tetap `null` dengan `origin=unknown`.
- Unknown spec key menambah kategori global deterministik dengan group `Tambahan`, `comparison=false`, `active=true`, dan order berikutnya. Nilai user/user-locked dipertahankan; kandidat berbeda menjadi suggestion.
- `tools/verify_dynamic_specs.py` memeriksa kategori, model ID, enam field provenance, kategori yatim, sumber/timestamp, field lama, user overwrite, dan idempotensi semantic+byte.
- `tools/gen_kompetitor.py` memanggil migrator sebelum menulis agar regenerasi berikutnya tidak menghapus fondasi dynamic specs. Generator tidak dijalankan karena membaca repo data terpisah yang dilarang tiket ini.
- `site/data/produk-katalog.json`, `tools/gen_data_js.py`, evidence taxonomy, UI/API, dan tiket 02-06 tidak diubah oleh implementasi ini.

### Bukti command dan output ringkas

```text
$ python -X utf8 tools\migrate_dynamic_specs.py
migrate_dynamic_specs: ditulis; models=102 categories=12 sha256=ca3ac5b20e5732ce974bf7ebe3172e50f9ab411586da56b5c1896d93559a2352
$ python -X utf8 tools\migrate_dynamic_specs.py
migrate_dynamic_specs: sudah sama (idempoten); models=102 categories=12 sha256=ca3ac5b20e5732ce974bf7ebe3172e50f9ab411586da56b5c1896d93559a2352
```

```text
$ python -X utf8 tools\verify_dynamic_specs.py
verify_dynamic_specs: models=102/102 brands=6/6
verify_dynamic_specs: categories=12 core=12 additional=0 duplicate_keys=0 orphan_categories=0
verify_dynamic_specs: invalid_sources=0 user_overwrites=0 lost_legacy_fields=0
verify_dynamic_specs: idempotent_semantic=true idempotent_bytes=true sha256=ca3ac5b20e5732ce974bf7ebe3172e50f9ab411586da56b5c1896d93559a2352
LULUS: 102/102 model valid; kategori yatim 0; overwrite user 0; field lama utuh
```

```text
$ python -X utf8 -m unittest discover -s tests -p test_dynamic_specs.py -v
Ran 8 tests in 0.012s
OK
```

```text
$ python -X utf8 tools\verify_product_detail.py
PASS verify_product_detail: embedded-first <1.2s with API delayed 4s, shared modal, canonical AQUA fallback enrichment, duplicate feature suppression, real 404 image fallbacks, edit isolation, keyboard, body-lock, 1440/390
```

```text
$ python -X utf8 D:\AI\tmp\win-temp\opencode\check_mtms_ticket01.py
LULUS: 102 model, 6 merek, kategori stabil, model_id unik, migrasi idempoten, verifier+tes hijau
```

## 2026-08-21 WIB - Koreksi Representasi Sparse

Klaim ukuran sebelumnya disupersede: 1.224 object `spec_values` memang valid secara bentuk, tetapi 1.122 di antaranya hanya materialisasi unknown kosong. Kontrak final tiket 01 memakai sparse representation: category key yang absent dibaca sebagai unknown/null oleh layer baca.

- Migrator sekarang hanya menyimpan state bermakna: value non-null, source/provenance, `origin=user`, `user_locked=true`, atau metadata ekstra yang perlu dipertahankan.
- Protected null tetap tersimpan dan tidak diisi kandidat; kandidat berbeda tetap masuk `research_suggestions`.
- Empty model menghasilkan `spec_values={}`. Empty unknown key dibuang dan tidak membuat kategori tambahan; unknown key bermakna tetap membuat kategori tambahan deterministik.
- Validator menerima category key yang absent, tetap menolak orphan/provenance invalid, dan kini juga menolak object unknown kosong yang dimaterialisasi.
- Generator tetap memakai migrator yang sama; tidak perlu perubahan tambahan pada `tools/gen_kompetitor.py`.

### Ukuran before/after

```text
BEFORE_BYTES=339718
AFTER_BYTES=121744
BYTES_SAVED=217974
BEFORE_LINES=12384
AFTER_LINES=3408
LINES_SAVED=8976
BEFORE_SPEC_RECORDS=1224
AFTER_SPEC_RECORDS=102
SPEC_RECORDS_REMOVED=1122
MEANINGFUL_RECORDS=102
EMPTY_UNKNOWN_RECORDS=0
```

### Bukti command

```text
$ python -X utf8 tools\migrate_dynamic_specs.py
migrate_dynamic_specs: ditulis; models=102 categories=12 sha256=69d506618c6f4dfd40c86efe8776040f2c1ab59f31ba7c34af738ef10fb6a048
$ python -X utf8 tools\migrate_dynamic_specs.py
migrate_dynamic_specs: sudah sama (idempoten); models=102 categories=12 sha256=69d506618c6f4dfd40c86efe8776040f2c1ab59f31ba7c34af738ef10fb6a048
```

```text
$ python -X utf8 tools\verify_dynamic_specs.py
verify_dynamic_specs: models=102/102 brands=6/6
verify_dynamic_specs: categories=12 core=12 additional=0 duplicate_keys=0 orphan_categories=0
verify_dynamic_specs: invalid_sources=0 user_overwrites=0 lost_legacy_fields=0
verify_dynamic_specs: sparse_records=102 empty_unknown_records=0
verify_dynamic_specs: idempotent_semantic=true idempotent_bytes=true sha256=69d506618c6f4dfd40c86efe8776040f2c1ab59f31ba7c34af738ef10fb6a048
LULUS: 102/102 model valid; kategori yatim 0; overwrite user 0; field lama utuh
```

```text
$ python -X utf8 -m unittest discover -s tests -p test_dynamic_specs.py -v
Ran 11 tests in 0.004s
OK
```

```text
$ python -X utf8 D:\AI\tmp\win-temp\opencode\check_mtms_ticket01.py
Ran 11 tests in 0.004s
OK
LULUS: 102 model, 6 merek, kategori stabil, model_id unik, migrasi idempoten, verifier+tes hijau
```

Learning untuk tiket ini: validator schema perlu memeriksa absence/default representation dan ukuran state, bukan hanya menyatakan setiap object yang dimaterialisasi valid.

## 2026-08-21 WIB - Audit Sesi Utama

- Sesi utama menjalankan ulang generator, migrator, validator, 11 unit test, verifier modal Produk/Kompetitor, dan dua kontrol negatif.
- Ditemukan perbedaan newline Windows antara generator dan migrator; `tools/gen_kompetitor.py` disamakan ke LF agar hash generator -> migrator -> generator identik.
- Hash akhir `site/data/kompetitor.json`: `69d506618c6f4dfd40c86efe8776040f2c1ab59f31ba7c34af738ef10fb6a048` pada ketiga tahap.
- Kontrol negatif kategori duplikat merah dan nilai user tetap terlindungi serta menghasilkan suggestion.
- Tiket 01 dinyatakan selesai lokal. Belum ada push/deploy/tulis data produksi untuk rangkaian fitur dinamis.

```text
SPEC_RECORDS=1224
PROVENANCE_FIELDS_MISSING=0
MOJIBAKE_LITERAL_MATCHES=0
LEGACY_FIELDS_LOST=0
LEGACY_VALUES_CHANGED=0
```

## 2026-08-21 WIB - Koreksi Lubang Tes User-Lock

Klaim bukti sebelumnya dikoreksi: fixture user lama memakai nilai non-null, sehingga tetap selamat melalui cabang existing-value walaupun pemeriksaan `protected` disabotase menjadi `False`. Tes itu belum membuktikan cabang perlindungan untuk nilai kosong.

- Ditambahkan focused regression dengan kandidat legacy tersedia dan existing `value=null` untuk dua pagar independen: `origin=user` serta `user_locked=true`.
- Pada behavior benar, kedua nilai tetap `null` dan kandidat masuk `research_suggestions`.
- Kontrol negatif dilakukan in-memory tanpa mengubah file migrator. Saat `protected=False`, kedua subkasus gagal karena nilai berubah menjadi `2 Pintu Top Mount`.
- SHA256 `tools/migrate_dynamic_specs.py` sebelum/sesudah tetap `EBD8B1A0321E472471930D19B83486857C3216C4B5EC436217F906E2694EAD87`.

```text
$ python -X utf8 -m unittest discover -s tests -p test_dynamic_specs.py -v
Ran 9 tests in 0.002s
OK
```

```text
$ negative control in-memory: protected=False
FAILED (failures=2)
NEGATIVE_CONTROL_LULUS: mutant protected=False ditolak; failures=2
```

```text
$ python -X utf8 tools\verify_dynamic_specs.py
verify_dynamic_specs: models=102/102 brands=6/6
verify_dynamic_specs: categories=12 core=12 additional=0 duplicate_keys=0 orphan_categories=0
verify_dynamic_specs: invalid_sources=0 user_overwrites=0 lost_legacy_fields=0
verify_dynamic_specs: idempotent_semantic=true idempotent_bytes=true sha256=ca3ac5b20e5732ce974bf7ebe3172e50f9ab411586da56b5c1896d93559a2352
LULUS: 102/102 model valid; kategori yatim 0; overwrite user 0; field lama utuh
```

```text
$ python -X utf8 D:\AI\tmp\win-temp\opencode\check_mtms_ticket01.py
Ran 9 tests in 0.004s
OK
LULUS: 102 model, 6 merek, kategori stabil, model_id unik, migrasi idempoten, verifier+tes hijau
```
