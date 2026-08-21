# Evidence: SAMSUNG and SHARP Specification Research

Researched: 2026-08-21 WIB (`+07:00`)

## Denominator and result

- Denominator: 34 exact target IDs: SAMSUNG 11 and SHARP 23.
- Records written: 34/34.
- Exact matches: 22/34: SAMSUNG 6/11 and SHARP 16/23.
- Statuses: complete 0, partial 22, unresolved 12.
- SAMSUNG: complete 0, partial 6, unresolved 5.
- SHARP: complete 0, partial 16, unresolved 7.
- Core values accepted: 195 of a possible 408 model-key cells.
- Every accepted value has `value`, `raw_value`, `source_url`, `source_kind`, and a timezone-bearing `verified_at`.

`complete` requires all 12 core keys. `partial` requires an exact model match and at least one verified core value. `unresolved` is used when the exact target or an explicit alias was not established.

## Core-key coverage

| Core key | SAMSUNG / 11 | SHARP / 23 | Combined / 34 |
|---|---:|---:|---:|
| `form_factor` | 6 | 16 | 22 |
| `door_count` | 5 | 16 | 21 |
| `freezer_position` | 4 | 0 | 4 |
| `gross_capacity_l` | 4 | 16 | 20 |
| `net_capacity_l` | 6 | 16 | 22 |
| `width_mm` | 6 | 16 | 22 |
| `height_mm` | 6 | 16 | 22 |
| `depth_mm` | 6 | 16 | 22 |
| `rated_power_w` | 0 | 5 | 5 |
| `compressor_type` | 5 | 0 | 5 |
| `cooling_system` | 6 | 16 | 22 |
| `defrost_type` | 4 | 4 | 8 |

Gross and net capacities remain separate. Capacity numbers without an explicit gross/net label were not assigned to either core key. SHARP power figures reported as `W/H`, `W/h`, `Watt/Hour`, or `Watt/Hours`, and numeric ranges, remain additional reported consumption data rather than `rated_power_w`.

## Source-kind counts

Counts below are provenance-bearing value occurrences, not unique URLs.

| Source kind | SAMSUNG | SHARP | Combined |
|---|---:|---:|---:|
| `official_product_page` | 76 | 178 | 254 |
| `official_business_product_page` | 19 | 0 | 19 |
| `official_promotion_pdf` | 2 | 0 | 2 |
| `official_catalog` | 0 | 2 | 2 |
| **Total** | **97** | **180** | **277** |

No accepted value required an unofficial retailer source. A retailer URL was checked for one SHARP mismatch but supplied no accepted value.

## Independent spot checks

- `SAMSUNG::RB30N4050B1_SE`: the Samsung Indonesia page shows the nearby code `RB30N4050B1/SE`, but does not explicitly declare the target underscore token as an alias. The target remains unresolved and no nearby-model values were copied.
- `SAMSUNG::RT35CG5420B1SE`: the Samsung Indonesia page explicitly shows the exact model, net 348 L, 600 x 1715 x 709 mm, Mono Cooling, No Frost, and Digital Inverter Compressor. Gross capacity and watts remain unresolved.
- `SHARP::SJ-236MN-HS`: the SHARP Indonesia page explicitly shows the exact model, gross/net 205/187 L, 545 x 1380 x 588 mm, 75 Watt, Fan Cooling Technology, and Automatic defrost.
- `SHARP::SJ-IF60PM-DS`: the SHARP Indonesia page explicitly shows the exact model, gross/net 523/466 L, 795 x 1800 x 740 mm, 180 W, and Fan Cooling System. The separate `40 Watt/Hours` note remains additional data and is not substituted for rated watts.

## Failures and unresolved targets

Exact identity was not established for these 12 target IDs, so no nearby-model specifications were copied:

- `SAMSUNG::RB30N4050B1_SE`: official source is `RB30N4050B1/SE`, without an explicit alias declaration for the underscore target token.
- `SAMSUNG::RF48A4000B4_SE`: official source is `RF48A4000B4/SE`, without an explicit alias declaration for the underscore target token.
- `SAMSUNG::RR18R1000SA_SE`: official source is `RR18R1000SA/SE`, without an explicit alias declaration for the underscore target token.
- `SAMSUNG::RT22FARBDBB1`: official source is `RT22FARBDB1/SE`; the extra `B` in the target was not proven as an alias.
- `SAMSUNG::RT25FARBDB1_SE`: official source is `RT25FARBDB1/SE`, without an explicit alias declaration for the underscore target token.
- `SHARP::SJ-IS50M-SL`: official source is `SJ-IS50MA-SL`.
- `SHARP::SJ-N182N`: official source is `SJ-N182N-HS`.
- `SHARP::SJ-N192N`: official source is `SJ-N192N-HS`.
- `SHARP::SJ-X165MG-GB_GR`: official source presents `SJ-X165MG-GB/GR`, without an explicit alias for the internal target token.
- `SHARP::SJ-X185MG-GB_GR`: sources present `SJ-X185MG-GB` or `SJ-X185MG-GB/GR`, without an explicit alias for the internal target token.
- `SHARP::SJ-X195MG-GB_GR`: official source presents `SJ-X195MG-GB/GR`, without an explicit alias for the internal target token.
- `SHARP::SJ316MGGB`: official source presents `SJ-316MG-GB/GR`.

Transport retries were capped at two attempts per URL:

- The Samsung consumer URL for `RT42CG6420B1SE` failed twice. The exact official Samsung Business page succeeded, so the product is partial rather than transport-unresolved.
- The initial SHARP URL for `SJ-426GI-GK` failed twice. The same official page with its version query parameter succeeded and showed the exact model, so the product is partial rather than transport-unresolved.
- No record was assigned a product verdict from a transport failure.

## Validation

The final machine check returned no errors for JSON parsing, top-level model counts, deterministic model sorting, required record keys, uniform checked-URL shape, allowed core keys, provenance shape, timezone-bearing timestamps, unresolved-core complements, and empty values on non-exact records.

Validated files:

- `research/specs-staging/SAMSUNG.json`
- `research/specs-staging/SHARP.json`
