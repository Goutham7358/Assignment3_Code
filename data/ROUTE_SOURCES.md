# Route schedule data and preparation

## Inputs

- `raw/route_schedules/`: 228 original DGCA approved domestic schedule publications from the existing project's archive, originally retrieved on 19 October 2026. Their dates and formats vary. Archive size does not imply complete airline or month coverage.
- `raw/route_schedule_manifest.json`: filenames, local paths relative to `data/`, original/official/retrieval URLs, byte counts and SHA-256 fingerprints. Each PDF is checked before extraction. No downloads are needed to reproduce this analysis.
- `raw/domestic_route_monthly.csv`: unchanged DGCA-derived city-pair passenger snapshot from [mkubicek/india-aviation-stats](https://github.com/mkubicek/india-aviation-stats/blob/16770ac59dae61ce7b80fd8bd67dd7f4cef280a6/data/processed/domestic_route_monthly.csv), pinned to commit `16770ac59dae61ce7b80fd8bd67dd7f4cef280a6`. SHA-256: `400e1b215682ded55d74168a8ef00d72016991d5c3f34ac8ca46eb555049b98e`. Its 134,958 directed records cover April 2015-July 2026. Only its 2025 observations select the top 20 pairs. It has no airline passenger split. The upstream MIT notice is in `LICENSE.txt`.
- `raw/route_coverage_gaps.csv`: reviewed gaps in the recovered filings, carried over from the submitted route methodology. These are documented source-coverage decisions, not gaps inferred from a missing airline row.
- `raw/route_month_exclusions.csv`: the two whole-month TruJet-related exclusions described below.
- `raw/route_operation_adjustments.json`: the earlier project's source URLs for the Jet/JetLite and Go First cessation conventions and Vistara/AIX merger treatment. The corresponding rules are explicit in `source/prepare_routes.py`.
- `raw/route_evidence/`: the two original parliamentary replies supporting the Jet/JetLite and Go First dates. `raw/route_evidence_manifest.json` records their URLs and fingerprints.
- `reference/route_monthly_before_trujet_review.csv`: the earlier project's 1,152-observation result, retained only for comparison. New EDA reads `processed/routes/route_monthly.csv`, which is rebuilt from the extraction.

The MIT notice applies to the upstream passenger dataset. Original schedule PDFs remain DGCA publications and retain their source attribution.

## PDF extraction

`source/extract_route_schedules.py` adapts the original economics project's `monthly_route_hhi.py` parser. Poppler's `pdftotext -bbox-layout` supplies word positions. The parser recognises the movement-table columns, airport headings, weekday masks and date intervals.

Across 4,187 PDF pages it extracts 189,980 movement rows. Only the 49,951 rows for the selected airport pairs are saved to `interim/routes/schedule_rows.csv`. Both arrival and departure records are preserved. Each row retains the PDF filename, page, printed row number and source URL. `interim/routes/source_manifest.json` records extraction status by publication; `extraction_issues.csv` preserves parser issues. There are 103 issues across all airports and no identified issues on the selected routes since 2019. Sixty publications have unsupported legacy tables or no readable year; they are not silently treated as valid data.

`interim/routes/extraction_summary.json` records these counts and the Poppler version. Every selected-route extracted row was compared field-for-field with the earlier project's saved extraction and agreed.

## Monthly preparation

`source/prepare_routes.py` does the following:

1. Rank airport pairs by the sum of both directions' passengers across all twelve months of 2025. Keep the same 20 pairs throughout; do not combine GOI and GOX.
2. Restrict each schedule row to both its printed validity and the seasonal boundaries. Expand weekdays into actual dates. Use April 2019-September 2026 as the O4 candidate period.
3. Deduplicate by airline, normalised flight number, calendar date and directed airport leg. Count departures at both ends to obtain the pair's both-direction total. Arrivals are used only for the endpoint check.
4. End Jet/JetLite records after 17 April 2019 and exclude Go First from 3 May 2023. Relabel Vistara UK flights as Air India AI-2 flights from 12 November 2024. The archived AIX integration treatment is recorded in the adjustments file.
5. Apply the ownership convention used nationally: AI + AI Express and Jet + JetLite throughout, adding Vistara and AirAsia/AIX Connect to AI Group from January 2022. The source's combined `AirAsia India / AIX Connect` label describes a renamed airline.
6. Require full-month source coverage. Compare arrivals and departures by airline within each pair-month. Keep observations only when the sum of absolute airline count differences divided by departures is at most 5%, and at least ten pairs pass in that month. This is the earlier pooled-endpoint screen, not the stricter directed check used in O3's regional extension.
7. Apply the two documented route-month exclusions before the monthly minimum-count rule. Keep missing observations missing.
8. Calculate ownership-group frequency HHI as the sum of squared percentage frequency shares. Brand HHI is calculated separately. CR2 adds the largest two ownership-group shares. Shares use unrounded counts; one route-month is one observation.

The review removes HYD-MAA in February and March 2022 as whole route-months because TruJet's archived plan continues beyond its suspension. This matches the O3 exclusion, without inventing replacement flights or partial-month service. [Contemporary reporting](https://www.ch-aviation.com/news/112730-indias-trujet-grounds-fleet-in-talks-for-25mn-funding), dated 18 February 2022, describes the suspension and a proposed restart. The exclusion is conservative; it does not assume an exact restart path from the available plans.

## Prepared outputs

All files below are in `processed/routes/`.

| File | Observation and main fields |
|---|---|
| `top20_routes.csv` | 20 airport pairs: 2025 rank, endpoint codes and both-direction annual passengers |
| `route_monthly.csv` | 1,150 retained pair-months: both-direction scheduled departures, brand/group frequency HHI, group CR2, leading group, group count and endpoint-quality measures |
| `airline_route_monthly.csv` | 5,647 airline-pair-months: ownership label, flights in each direction, both-direction count, route denominator and airline percentage frequency share |
| `group_route_monthly.csv` | 4,884 group-pair-months: group rank, flights, route denominator and group percentage frequency share |
| `route_coverage.csv` | 1,800 candidate pair-months: source-coverage flag, retained flag and exclusion reason |
| `route_monthly_before_screen.csv` | 1,404 observations before endpoint, operational-exclusion and monthly minimum-count screening |
| `source_pdfs_used.csv` | The 92 PDFs contributing departure rows to retained observations, with original URLs and fingerprints |
| `preparation_summary.json` | Sample counts, periods, thresholds and deduplication count |
| `verification.json` | Results from the separate source/earlier-result/SQL/worked-example checks |

Dates use `YYYY-MM`. Flight fields count approved scheduled departures, not passengers. Frequency shares and `group_cr2_pct` are percentages on a 0-100 scale. HHI is on a 0-10,000 scale. `endpoint_absolute_count_difference` sums absolute airline differences; `endpoint_difference_pct` divides that sum by the departure total and multiplies by 100. Boolean flags are written as `True`/`False`.

The retained panel spans 66 observed months within 90 calendar months, April 2019-September 2026. Each observed month has 12-20 pairs; 14 months have all 20. There are 303 exact-endpoint-match observations. The two TruJet exclusions account for the entire change from the earlier 1,152-observation panel. All other retained flight totals, HHI values and CR2 values agree, allowing for the earlier CSV's display rounding.

## Checks and limits

Run `python3 data/source/verify_routes.py` to check the 228 PDF fingerprints, compare the 1,150 retained observations with the earlier project, and independently recompute every group HHI using SQL on the airline counts. Its Delhi-Pune example checks June 2026: 120 Akasa flights and 1,430 flights across all airlines. The underlying Akasa Summer 2026 PDF, pages 9 and 17, supplies complementary weekday rows and both directions.

The EDA histogram pools pair-months with equal weight. It does not weight by passengers or flights; pairs with more usable months appear more often. Histogram intervals have width 500 HHI points, include their left edge, and exclude the right edge except the final interval, which includes 10,000. Quartiles use linear interpolation. Coverage bars count retained pairs; a zero means no usable observation, not no air service. Missing HHI values are never set to zero.

Approved schedules can differ from operation. Whole missing carrier filings can escape the endpoint comparison, and the chosen major routes do not represent India's entire network. Frequency shares cannot recover route airline passenger shares. This step describes sample coverage and concentration; it does not assess H6 or establish market power.
