# AQUA Product-Extra Specification Research Evidence

- Researched at: 2026-08-21T21:00:00+07:00
- Scope: `product_extra`
- Denominator: **10** models
- Exact matches: **5/10**
- Complete / partial / unresolved: **0 / 5 / 5**
- AQUA catalog **42** minus competitor AQUA **32** equals **10**.
- Zero overlap with `AQUA.json`: **verified (0 models)**.

## Exact Set Difference

The exact, sorted 10-model set difference is:

1. AQR-320RBG
2. AQR-350RBG
3. AQR-CTD506RBC
4. AQR-CTD506RBG
5. AQR-DTM248CBP
6. AQR-DTM268CBP
7. AQR-DTM288CBP
8. AQR-TSE696RAV
9. AQR-TTD546RBG
10. AQR-TTD546RBV

## Values Per Core Key

| Core key | Values | Missing |
|---|---:|---:|
| form_factor | 3 | 7 |
| door_count | 2 | 8 |
| freezer_position | 2 | 8 |
| gross_capacity_l | 0 | 10 |
| net_capacity_l | 1 | 9 |
| width_mm | 1 | 9 |
| height_mm | 1 | 9 |
| depth_mm | 1 | 9 |
| rated_power_w | 0 | 10 |
| compressor_type | 3 | 7 |
| cooling_system | 5 | 5 |
| defrost_type | 0 | 10 |

## Source-Kind Counts

- official_product_page: 24 values

## Source Failures

- official_manual https://aquaelektronik.com/pdfs/0060528988.pdf | affected: AQR-320RBG, AQR-350RBG | web extractor exceeded 5 MB; direct retry returned HTTP 403
- official_sitemap | affected: catalog discovery | transport error
- official_product_page https://aquaelektronik.com/product/detail/772/AQR-DTM288CB%28BE%29 | affected: AQR-DTM288CBP | HTTP 404

## Method Notes

- Exact identity required the requested model code on its exact official product page.
- Gross and net capacity were accepted only from explicitly labelled fields; unlabelled capacities remain unresolved.
- Nearby variants were not promoted, and no values were copied without an explicit alias.
- Records and the set-difference list are sorted deterministically by exact model string (code-point order).
- Source-kind counts include every populated entry in `specs` and `additional_specs`; a list-valued entry counts once.
