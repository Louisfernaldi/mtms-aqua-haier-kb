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

## 2026-08-21 WIB - Implementasi Tiket 02 API dan Editor Dinamis

Status: **implementasi lokal/offline selesai dan checker security host hijau. Belum ada commit, push, deploy, secret read, atau tulis API live**.

### Kontrak endpoint

- Semua route tetap berada di belakang `functions/_middleware.js`; request API tanpa cookie login berhenti `401` sebelum handler.
- `GET /api/spec-categories`, `GET /api/kompetitor`, dan `GET /api/produk` mengembalikan data live beserta `ETag` dan `X-Data-SHA`. Bentuk body data model lama tetap dipertahankan.
- `PATCH /api/spec-categories` menerima `create_category` dan `update_category`. Key immutable; duplicate key/order ditolak; kategori core tidak dapat di-rename, dihapus, dinonaktifkan, dikeluarkan dari comparison, atau diurut ulang. Kategori tambahan dapat diubah label/group/unit/active/order/comparison tanpa membuat orphan.
- `PATCH /api/kompetitor` dan `PATCH /api/produk` menerima `set_spec_value`, `set_features`, `update_model`, `submit_research`, `accept_suggestion`, dan `reject_suggestion` dengan exact `model_id=brand::model`. **Accepted authorization design sesuai LAPORAN line 207:** password edit terpisah dihapus; setelah sekali login existing berhasil, user langsung boleh mengedit. `If-Match` tetap pagar konkurensi agar snapshot stale tidak menulis, bukan mekanisme authorization/login.
- Edit value user selalu ditulis `origin=user` dan `user_locked=true`. Research hanya mengisi slot kosong yang tidak terlindungi; nilai berbeda masuk `research_suggestions` berstatus `pending`. Accept/reject mengubah status secara eksplisit; accept menjadi value user-locked dengan provenance sumber tetap utuh.
- Semua `PATCH` dan editor `PUT` lama wajib membawa `If-Match`/base SHA. SHA hilang berhenti `428`, stale berhenti `412`, dan konflik GitHub `409/422` dipetakan ke `412` tanpa retry otomatis.
- Validasi server meliputi action/payload, scalar value, exact model, kategori yatim, duplicate key/order, URL `http/https`, timestamp bertimezone, source research lengkap, bullet, provenance, dan status suggestion.

### Editor minimal

- `site/kompetitor.html` memuat satu panel samping tiket 02 melalui `site/js/dynamic-spec-editor.js`; render fallback, tabel pembanding, dan modal detail existing tidak diubah.
- Tombol editor disabled sampai GET data kompetitor + kamus kategori live sama-sama sukses dan membawa SHA. Error boot terlihat jelas; stale write tidak diulang dan meminta user menekan `Muat ulang`.
- Panel memilih exact model dari 102 record, mengedit sparse `spec_values` per kategori dan bullet `Fitur Unggulan`, menampilkan origin/user-lock/sumber/waktu verifikasi, serta menyediakan accept/reject hanya untuk suggestion pending.
- Panel kategori global mendukung tambah dan edit label/group/unit/active/order/comparison. Key tidak dapat diedit/dihapus; pagar core juga terlihat dan ditegakkan lagi di server.

### Bukti offline putaran 1

```text
$ node --check functions/_lib/dynamic-specs.js
$ node --check functions/api/spec-categories.js
$ node --check functions/api/produk.js
$ node --check functions/api/kompetitor.js
$ node --check site/js/dynamic-spec-editor.js
$ node --check site/js/produk.js
seluruhnya exit=0
```

```text
$ node --test tests/dynamic-specs-api.test.mjs
tests 11; pass 11; fail 0
```

```text
$ python -X utf8 -m unittest tests.test_dynamic_specs
Ran 11 tests in 0.021s
OK
```

```text
$ python -X utf8 tools/verify_dynamic_specs.py
verify_dynamic_specs: models=102/102 brands=6/6
verify_dynamic_specs: sparse_records=102 empty_unknown_records=0
verify_dynamic_specs: editor_wiring=true
LULUS: 102/102 model valid; kategori yatim 0; overwrite user 0; field lama utuh
```

Tes endpoint memakai `fetch` palsu hanya pada boundary jaringan. Kasus unauthorized, invalid input, duplicate key, stale SHA, user lock, research conflict, accept, reject, dan satu write sukses semuanya tidak pernah mengakses jaringan hidup; body write yang tertangkap juga membuktikan SHA lama diteruskan ke GitHub mock.

### Koreksi setelah gerbang putaran 2

Checker independen tetap memiliki SHA256 `195473FCAFAF177E62EEA3DF4FDD44A1330F0CD04175C304BB75CB48709B49EE` dan tidak disentuh. Pada eksekusi checker, unit Python dan `verify_dynamic_specs` lulus, lalu `verify_product_detail` berhenti karena penanda kompatibilitas lama `MTMS_COMPETITOR_LIVE_READY` tidak menjadi `true` saat fixture GET sukses tanpa header SHA.

Penyebabnya bukan kegagalan render atau write guard: implementasi sempat menyamakan “GET API selesai” dengan “SHA tersedia”. Koreksi terakhir memulihkan arti penanda lama untuk Produk dan Kompetitor menjadi GET selesai, sementara semua write lama tetap fail-closed bila SHA kosong dan panel dinamis tiket 02 tetap disabled sampai GET data + kategori sama-sama memberi SHA. Checker tidak diulang di sesi ini karena instruksi membatasi dua putaran.

Command host yang perlu dijalankan dari root repo:

```text
python -X utf8 D:\AI\tmp\win-temp\opencode\check_mtms_ticket02.py
```

### Koreksi host - GET kategori harus bergantung pada SHA data

Host berikutnya menemukan `verify_product_detail` merah karena console 404 pada 1440px. Akar terverifikasi: `loadLive()` memakai `Promise.all`, sehingga `api/spec-categories` langsung diminta walaupun fixture existing hanya menyediakan `api/kompetitor` tanpa SHA.

Koreksi kode mengubah alur menjadi serial dan fail-closed:

1. GET data model terlebih dahulu.
2. Bila respons data gagal atau tidak membawa `ETag`/`X-Data-SHA`, editor tetap disabled, menampilkan pesan, dan berhenti tanpa request kategori.
3. Hanya respons data dengan SHA yang membuka GET kamus kategori.
4. Editor baru aktif setelah kedua GET valid; seluruh PATCH/PUT tetap wajib `If-Match` dan tidak memiliki retry otomatis.

Regression offline ditambahkan pada `tests/dynamic-specs-api.test.mjs` dengan loader terisolasi: respons data sukses tetapi `sha=""` harus reject dan daftar URL yang dipanggil wajib persis hanya `api/kompetitor`. Tes/checker tidak dijalankan oleh sesi ini sesuai instruksi; host yang mengulang gerbang eksternal.

## 2026-08-21 WIB - Gapfix Audit Tiket 02

Status: **implementasi dan verifier lokal hijau; tanpa commit, push, deploy, secret read, atau API live**.

### Gap 1 - Editor reusable di Kompetitor dan Produk

- `dynamic-spec-editor.js` sekarang menerima dua bentuk payload: object `{brands:[...]}` Kompetitor dan array Produk. Array tanpa `brand` dibentuk exact sebagai `AQUA::model`.
- `site/produk.html` memuat editor dinamis yang sama. Loader existing `site/js/produk.js` melakukan mount ke `api/produk` setelah data live selesai; editor Produk lama tetap utuh dan tetap punya pagar SHA sendiri.
- Regression memakai array Produk berisi tepat 42 model. PATCH mock ke `/api/produk` hanya mengubah exact `AQUA::PRODUK-42`; `LG::PRODUK-42` ditolak `404`.

### Gap 2 - Tidak ada duplicate model GET

- Loader existing halaman menjadi satu-satunya pemilik GET `api/kompetitor` atau `api/produk`.
- Mount editor wajib menerima `initialData` dan `initialSha`; editor membuat clone lokal lalu hanya GET `api/spec-categories`.
- Bila payload atau SHA awal kosong, editor disabled dan tidak melakukan request apa pun. Tombol reload hanya memuat ulang kategori dari payload+SHA yang sudah ada, bukan GET model baru.
- Regression call-count membuktikan initial Produk 42 hanya menghasilkan daftar panggilan `['api/spec-categories']`; tidak ada `api/produk` maupun `api/kompetitor` dari editor.

### Gap 3 - User lock dan suggestion untuk bullet fitur

- `fitur[]` tetap array utama dan tidak menjadi spec category. Metadata terpisah disimpan sebagai `fitur_meta`: `origin`, `user_locked`, `source_url`, `source_kind`, dan `verified_at`.
- Action `set_features` dan field `fitur` dalam `update_model` selalu menulis `origin=user` serta `user_locked=true`, termasuk edit eksplisit menjadi array kosong.
- Action `submit_research_features` wajib membawa URL http/https, `source_kind`, dan timestamp bertimezone. Konflik dengan fitur user-locked tidak overwrite; kandidat masuk `feature_suggestions[]` berstatus `pending`.
- `accept_feature_suggestion` mengganti bullet secara eksplisit, mempertahankan provenance riset, lalu mengunci hasil sebagai user. `reject_feature_suggestion` hanya menandai rejected dan mempertahankan bullet user.
- Validator server memeriksa bentuk array utama, metadata, origin/lock, provenance, status, dan seluruh feature suggestion. Tampilan editor meng-escape bullet/status/sumber dan hanya membuat link untuk URL http/https yang aman.

### Bukti offline gapfix

```text
$ node --check functions/_lib/dynamic-specs.js
$ node --check functions/api/produk.js
$ node --check site/js/dynamic-spec-editor.js
$ node --check site/js/produk.js
$ node --check tests/dynamic-specs-api.test.mjs
seluruhnya exit=0
```

```text
$ node --test tests/dynamic-specs-api.test.mjs
tests 19; pass 19; fail 0
```

```text
$ python -X utf8 -m unittest tests.test_dynamic_specs
Ran 11 tests
OK
```

```text
$ python -X utf8 tools/verify_dynamic_specs.py
verify_dynamic_specs: models=102/102 brands=6/6
verify_dynamic_specs: editor_wiring=true
LULUS: 102/102 model valid; kategori yatim 0; overwrite user 0; field lama utuh
```

```text
$ python -X utf8 tools/verify_product_detail.py
PASS verify_product_detail: embedded-first <1.2s, shared modal, edit isolation, keyboard, body-lock, 1440/390
```

```text
$ python -X utf8 D:\AI\tmp\win-temp\opencode\check_mtms_ticket02_gapfix.py
[python unit] exit=0
[dynamic verifier] exit=0
[product detail verifier] exit=0
[offline JS tests] exit=0 (19/19)
[seluruh node --check] exit=0
[git diff --check] exit=0
LULUS: gapfix tiket 02 melewati seluruh gerbang host
```

Checker eksternal tetap read-only dan SHA256 sebelum eksekusi adalah `D5C5F5B610A676FD4A3427F7351B466AFE34807BBAF65477A4C2514DC117AA50`.

## 2026-08-21 WIB - Koreksi parity full PUT Produk

- `PUT /api/produk` kini, setelah base SHA terbukti fresh, membaca kamus kategori dan menjalankan `prepareModelDocument(..., true)` atas seluruh array sebelum GitHub write.
- Full array legacy tanpa state dinamis tetap diterima lalu diperkaya exact `model_id=AQUA::model`, sparse `spec_values={}`, suggestion kosong, serta `fitur_meta` kompatibel; field legacy lain tetap dipertahankan.
- State dinamis yang sudah ada divalidasi penuh. Orphan category maupun metadata invalid menghasilkan `400` dan zero GitHub write; stale SHA menghasilkan `412` sebelum baca kategori/write.
- Regression endpoint offline ditambahkan untuk legacy + model baru, dua state invalid, dan stale SHA. Seluruh boundary jaringan dimock; checker host belum dijalankan dalam sesi ini.
- Checker eksternal tetap tidak disentuh; SHA256 terverifikasi `7D3FA2DB56DEB57ED8E7C2DC24163CCCB44748E0E624DE291E2F83CDEA823D5F`.

## 2026-08-21 WIB - Penutupan security Tiket 02

- Browser Chromium nyata menerima payload API `img onerror`, kombinasi kutip, dan URL `javascript:`. Marker eksekusi tetap `0`, elemen/event injeksi `0`, URL JavaScript di DOM `0`, serta fase payload punya `0` console/page error.
- `saveData` memakai satu lock serial. Respons `412` tidak di-retry dan memicu reload halaman penuh agar data, SHA, dan state seluruh editor kembali dari snapshot live terbaru.
- Regression mencakup empty payload, penghapusan 50%, penghapusan brand, satu edit sah, recursive oversized zero-network, dan race lock; `node --test` lulus `26/26`.
- `python -X utf8 D:\AI\tmp\win-temp\opencode\check_mtms_ticket02_security.py` lulus seluruh gerbang: unit Python, offline JS, dua verifier existing, browser E2E, seluruh `node --check`, dan `git diff --check`.

## 2026-08-21 WIB - Koreksi audit host lanjutan Tiket 02

Status: **lima gap audit diperbaiki; seluruh gerbang lokal dan host checker final hijau**.

- Legacy Produk tidak lagi menambahkan `foto_list` turunan sebagai properti enumerable. UI tetap dapat merender daftar foto, tetapi full PUT 42 item tidak mengirim perubahan turunan pada semua model; tepat satu edit user tetap terdeteksi sebagai satu edit oleh guard server.
- Regression eksplisit membuktikan satu delete valid, dua model edit invalid, dan endpoint dua-edit berhenti `400` dengan zero GitHub PUT. One-model guard tidak dilonggarkan.
- URL gambar tersimpan kini hanya menerima `http:`, `https:`, atau path relatif same-origin. `data:` dan `javascript:` ditolak di UI dan server; upload file hanya menghasilkan preview lokal tanpa menulis data URL ke input atau payload tersimpan.
- Jalur `412` mengosongkan `compSha`, menurunkan `liveReady` dan `MTMS_COMPETITOR_LIVE_READY`, lalu meng-invalidasi save sequence sebelum menjadwalkan reload. Tidak ada retry otomatis.
- Accepted authorization design tetap sesuai LAPORAN line 207: password edit terpisah dihapus dan sekali login existing berhasil langsung boleh edit. `If-Match` hanya pagar konkurensi snapshot, bukan authorization.
- `node --test tests/dynamic-specs-api.test.mjs`: **32/32 lulus**. Browser Chromium nyata: marker/event/injected element/JavaScript URL `0`, payload console/page error `0`, stored `data:image` tidak masuk DOM, preview lokal tidak tersimpan, satu PUT stale tanpa retry, serta `liveReady=false` terbukti sebelum reload.
- Unit Python **11/11**, dynamic verifier **102/102**, product-detail verifier, dan seluruh targeted `node --check` lulus. Tidak ada network eksternal, write live, commit, push, deploy, atau pembacaan secret.
- `python -X utf8 D:\AI\tmp\win-temp\opencode\check_mtms_ticket02_security.py` exit `0`: seluruh unit, regression 32/32, dua verifier existing, browser security E2E, targeted syntax checks, dan `git diff --check` hijau. Checker eksternal tidak diubah.
