# Airline traffic data

## Source and version

- Original authority: Directorate General of Civil Aviation (DGCA), Government of India.
- Normalised distribution: [mkubicek/india-aviation-stats](https://github.com/mkubicek/india-aviation-stats).
- Pinned upstream commit: `16770ac59dae61ce7b80fd8bd67dd7f4cef280a6`.
- [Upstream file at that commit](https://github.com/mkubicek/india-aviation-stats/blob/16770ac59dae61ce7b80fd8bd67dd7f4cef280a6/data/processed/carrier_monthly.csv).
- Snapshot originally downloaded for the project on 20 September 2026.
- SHA-256: `30412b650b47b9d8ba50917365b29f120f2da458403533829d65fd11b64c09be`.
- Upstream licence: MIT; the supplied notice is preserved in `LICENSE.txt`.

`carrier_monthly.csv` is copied unchanged from the existing economics project. It is already a cleaned distribution of DGCA workbooks, rather than an original DGCA workbook or a dataset newly cleaned in this repository.

## What one row means

One airline, one service type and one calendar month. The file has 3,482 rows and covers January 2015-July 2026. It includes domestic/international and scheduled/non-scheduled services.

For the agreed national analysis, keep `service_type == "scheduled_domestic"` and positive passenger counts. This retains 1,577 airline-months across 138 observed months. April 2020 has no retained observation; it must not be inserted as a zero-concentration month.

## Fields needed for the first figure

| Column | Meaning |
|---|---|
| `airline` | Operating airline brand |
| `service_type` | Service category used to select scheduled domestic traffic |
| `year`, `month` | Calendar period |
| `passengers` | Passenger journeys carried; not unique people |

The first script will calculate passenger shares after applying the study's dated ownership grouping. The two largest groups must be identified afresh each month, rather than assuming the same two groups throughout the series.

## Other fields and limits

The file also contains passenger-kilometres, seat-kilometres, load factors and freight measures. Passenger-km and seat-km are reported in thousands. There are positive-passenger records with zero passenger-km/seat-km for Air Odisha in September 2018 and Air Deccan in March 2020; capacity analyses will need to document their treatment.

This file has no airline-by-route breakdown, fares or marginal costs. National concentration measures cannot establish route passenger shares, pricing power or consumer harm.
