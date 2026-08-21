# AQUA + LG Specification Research Evidence

- Researched at: 2026-08-21T19:53:29.748+07:00
- Denominator: **48** models (AQUA 32, LG 16)
- Exact matches: **48/48**
- Complete / partial / unresolved: **0 / 48 / 0**

## Values Per Core Key

| Core key | Values | Missing |
|---|---:|---:|
| form_factor | 24 | 24 |
| door_count | 24 | 24 |
| freezer_position | 12 | 36 |
| gross_capacity_l | 13 | 35 |
| net_capacity_l | 13 | 35 |
| width_mm | 14 | 34 |
| height_mm | 14 | 34 |
| depth_mm | 14 | 34 |
| rated_power_w | 0 | 48 |
| compressor_type | 38 | 10 |
| cooling_system | 31 | 17 |
| defrost_type | 10 | 38 |

## Source-Kind Counts

- official_product_page: 345 values

## Source Failures

- official_manual https://aquaelektronik.com/pdfs/0060528988.pdf | affected: AQR-350RBM | web extractor exceeded 5 MB; direct retry returned HTTP 403
- official_manual https://aquaelektronik.com/pdfs/0060528367.pdf | affected: AQR-355IG, AQR-355IM | web extractor exceeded 5 MB; direct retry returned HTTP 403
- official_manual https://aquaelektronik.com/pdfs/0060531413.pdf | affected: AQR-382IM | web extractor exceeded 5 MB; direct retry returned HTTP 403

## Method Notes

- Exact identity required the requested model on its exact official product page; model records use only existing IDs from site/data/kompetitor.json.
- Gross and net capacity were accepted only from explicitly labelled fields. Unlabelled litres remain unresolved and are noted per record.
- Marketing technology names are retained as official feature evidence or explicit cooling/compressor names, not promoted to unrelated core equivalences.
- Product-page transport was attempted at most twice. Transport failures do not become product verdicts.
- Records are sorted deterministically by exact model string (code-point order).
