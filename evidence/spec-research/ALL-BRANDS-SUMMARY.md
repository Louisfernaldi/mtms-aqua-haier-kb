# All-Brands Specification Research Merge Summary

Snapshot deterministik tiket 03; seluruh sumber berasal dari tujuh JSON staging lokal.

## Denominator Riset

- Unique target: **112/112**
- Exact / partial / unresolved: **92 / 92 / 20**
- Complete: **0**
- Duplicate identity / record missing: **0 / 0**

## Hasil Apply Lokal

- Target model applications: **144** (Kompetitor 102 + Produk 42)
- Exact applications / skipped non-exact: **124 / 20**
- Applied values: **885**
- Conflicts / pending suggestions: **36 / 36**
- Protected values preserved: **0**
- Single semantic contract: 12 kategori inti tetap pertama; 29 kategori tambahan di-append ke `spec_categories`, dan seluruh nilai sparse hidup di `spec_values`.

### kompetitor

- Models / exact / skipped: 102 / 87 / 15
- Applied / conflicts / suggestions: 767 / 24 / 24

| Core key | Applied |
|---|---:|
| `compressor_type` | 57 |
| `cooling_system` | 56 |
| `defrost_type` | 25 |
| `depth_mm` | 52 |
| `door_count` | 59 |
| `form_factor` | 39 |
| `freezer_position` | 16 |
| `gross_capacity_l` | 33 |
| `height_mm` | 52 |
| `net_capacity_l` | 35 |
| `rated_power_w` | 22 |
| `width_mm` | 52 |

| Additional key | Applied |
|---|---:|
| `active_fresh_filter` | 3 |
| `approximate_power_consumption_w_per_hour` | 2 |
| `automatic_ice_maker` | 11 |
| `capacity_unlabelled_l` | 17 |
| `compressor_warranty` | 1 |
| `dimensions_unlabelled` | 1 |
| `dispenser_type` | 1 |
| `door_alarm` | 13 |
| `door_material` | 12 |
| `energy_consumption_kwh_year` | 7 |
| `energy_star_rating` | 1 |
| `exterior_color` | 14 |
| `flexzone` | 1 |
| `gross_freezer_capacity_l` | 2 |
| `gross_refrigerator_capacity_l` | 2 |
| `gross_weight_kg` | 10 |
| `marketing_features` | 16 |
| `net_freezer_capacity_l` | 5 |
| `net_refrigerator_capacity_l` | 5 |
| `net_weight_kg` | 14 |
| `official_features` | 48 |
| `optimal_fresh_zone` | 3 |
| `power_consumption_reported` | 10 |
| `refrigerant` | 30 |
| `smartthings_app_support` | 2 |
| `water_dispenser` | 8 |
| `weight_kg` | 13 |
| `wifi` | 13 |
| `wifi_embedded` | 4 |

| Source kind | Applied |
|---|---:|
| `official_archive` | 16 |
| `official_business_product_page` | 18 |
| `official_catalog` | 2 |
| `official_page` | 144 |
| `official_product_page` | 585 |
| `official_promotion_pdf` | 2 |

### produk-katalog

- Models / exact / skipped: 42 / 37 / 5
- Applied / conflicts / suggestions: 118 / 12 / 12

| Core key | Applied |
|---|---:|
| `compressor_type` | 27 |
| `cooling_system` | 23 |
| `defrost_type` | 3 |
| `depth_mm` | 2 |
| `door_count` | 15 |
| `freezer_position` | 6 |
| `height_mm` | 2 |
| `net_capacity_l` | 1 |
| `width_mm` | 2 |

| Additional key | Applied |
|---|---:|
| `official_features` | 37 |

| Source kind | Applied |
|---|---:|
| `official_product_page` | 118 |

## SHA-256 Outputs

| Output | Bytes | SHA-256 |
|---|---:|---|
| `site/data/kompetitor.json` | 417216 | `0923cf012f98c354c6c36f68ea82f913d9dcb4c9ee06f8adf32a76c426d700a1` |
| `site/data/produk-katalog.json` | 123359 | `bd4f960874a93f1a6a0b0a173f2e62a241f91f671c94d96f2161dff8b5449cca` |
| `site/data/spec-categories.json` | 8054 | `5a6629353abb2c2e8028e24da92bf35991e4b78439d022a0bb28e6b48a359c69` |

Non-exact records tidak diterapkan. Notes tidak pernah menjadi fitur atau spesifikasi; hanya `specs` dan `additional_specs` eksplisit yang diproses.
