# Evidence: MIDEA and POLYTRON Specification Research

Researched at: `2026-08-21T19:48:07+07:00`

## Denominator and outcomes

- Denominator: 20 exact repository model IDs, comprising MIDEA 7 and POLYTRON 13.
- Exact matches: 17/20 (MIDEA 7/7; POLYTRON 10/13).
- Statuses: `complete` 0, `partial` 17, `unresolved` 3.
- Every discovered value has `raw_value`, `source_url`, `source_kind`, and a `+07:00` timestamp.
- No unlabelled capacity was mapped to `gross_capacity_l` or `net_capacity_l`.

## Core-value coverage

| Model ID | Status | Exact | Core values found |
|---|---|---:|---|
| MIDEA::MDRF550FGF28ID | partial | yes | form_factor, width_mm, height_mm, depth_mm, rated_power_w, compressor_type |
| MIDEA::MDRS710FGF28ID | partial | yes | form_factor, rated_power_w, compressor_type |
| MIDEA::MDRT345MTB30 | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, compressor_type |
| MIDEA::MDRT385MTB30 | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, compressor_type |
| MIDEA::MDRT611EVD28ID | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, compressor_type, defrost_type |
| MIDEA::MDRT611EVD50ID | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, compressor_type, defrost_type |
| MIDEA::MDRU288FZG02ID | partial | yes | form_factor, width_mm, height_mm, depth_mm, rated_power_w, compressor_type, cooling_system |
| POLYTRON::PRA_18DMY | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, defrost_type |
| POLYTRON::PRB_159B_R | unresolved | no | none |
| POLYTRON::PRB_179R_B | unresolved | no | none |
| POLYTRON::PRB_219R | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, defrost_type |
| POLYTRON::PRB_25MNX | unresolved | no | none |
| POLYTRON::PRM_495X | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, compressor_type |
| POLYTRON::PRS_455S | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, compressor_type |
| POLYTRON::PRS_465X | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, compressor_type, cooling_system |
| POLYTRON::PRS_510X | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, compressor_type |
| POLYTRON::PRS_521Y | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, compressor_type, defrost_type |
| POLYTRON::PRS_551X | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, compressor_type, cooling_system |
| POLYTRON::PRW_23MNX | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, defrost_type |
| POLYTRON::PRW_29VX | partial | yes | form_factor, door_count, width_mm, height_mm, depth_mm, rated_power_w, compressor_type, defrost_type |

## Values per core key

| Core key | Values found / 20 |
|---|---:|
| form_factor | 17 |
| door_count | 14 |
| freezer_position | 0 |
| gross_capacity_l | 0 |
| net_capacity_l | 0 |
| width_mm | 16 |
| height_mm | 16 |
| depth_mm | 16 |
| rated_power_w | 17 |
| compressor_type | 14 |
| cooling_system | 3 |
| defrost_type | 7 |

All 17 exact-match pages publish only an unqualified `Capacity`; these values are retained as `additional_specs.capacity_unlabelled_l`, not counted as gross or net.

## Source-kind counts

Counts below are provenance-bearing values across both `specs` and `additional_specs`, not URL visits.

| Source kind | Value count |
|---|---:|
| official_page | 153 |
| official_archive | 16 |
| official_search | 0 |
| retailer / other | 0 |

Official search pages were used only to test identity mismatches and therefore contributed no specification values.

## Failures and exclusions

- `POLYTRON::PRB_159B_R`: starting URL is PRB 159R; official search returns distinct PRB 159B and PRB 159Y entries. No explicit alias joined the composite target to one product.
- `POLYTRON::PRB_179R_B`: starting URL and search result identify PRB 179R only. The `_B` suffix was not documented as an alias.
- `POLYTRON::PRB_25MNX`: starting URL is PRW 25MNX/PRW 25MNXC; official search found no PRB 25MNX. This is a brand-prefix mismatch, not a fuzzy match.
- `POLYTRON::PRS_455S`: the current official product URL returned HTTP 404 on two attempts. An exact archived official page was recovered and used. The failed current URL is a source-page failure, not a product verdict.
- MIDEA MDRS710FGF28ID: exact official page was available only from an archived capture. Its dimension order was not labelled, so dimensions remain additional unresolved data instead of being assigned by convention.
- Generic Polytron feature blocks that named PRS 451Y, PRS 460B, PRS 561X, or PRW 296Y were excluded from other exact-model records.
- `Multi Air Flow` marketing labels were not automatically equated to `cooling_system`; only source wording that explicitly described a system/technology for the exact model was retained.
