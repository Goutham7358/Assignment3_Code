# Airline traffic data

This page covers the national passenger file. Route schedules, selection data and preparation are documented in [ROUTE_SOURCES.md](ROUTE_SOURCES.md).

## Source and version

- Original authority: Directorate General of Civil Aviation (DGCA), Government of India.
- Normalised distribution: [mkubicek/india-aviation-stats](https://github.com/mkubicek/india-aviation-stats).
- Pinned upstream commit: `16770ac59dae61ce7b80fd8bd67dd7f4cef280a6`.
- [Upstream file at that commit](https://github.com/mkubicek/india-aviation-stats/blob/16770ac59dae61ce7b80fd8bd67dd7f4cef280a6/data/processed/carrier_monthly.csv).
- Snapshot originally downloaded for the project on 20 September 2026.
- SHA-256: `30412b650b47b9d8ba50917365b29f120f2da458403533829d65fd11b64c09be`.
- Upstream licence: MIT; the supplied notice is preserved in `LICENSE.txt`.

`raw/carrier_monthly.csv` is copied unchanged from the existing economics project. It is already a cleaned distribution of DGCA workbooks, rather than an original DGCA workbook or a dataset newly cleaned in this repository.

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

`source/prepare_national.py` retains positive scheduled-domestic passenger observations, checks unique airline-months, and adds an ISO month and ownership-group label. It writes `processed/national_airline_monthly.csv` (1,577 rows) and an audit file. It excludes 1,773 rows for other service types and 132 scheduled-domestic rows with zero passengers. No observations are interpolated or winsorised.

The ownership convention is the one submitted in Assignment 2:

- Air India and Air India Express are combined throughout.
- Jet Airways and JetLite are combined throughout.
- From January 2022, Vistara, AirAsia India and AIX Connect join the Air India Group. Before that month the Tata joint ventures remain separate.
- Other airline labels are retained.

This is the study's monthly grouping convention, not a reconstruction of every ownership interest. In particular, the January 2022 series movement includes reclassification.

`O4/EDA/eda_national.py` sums passengers within these groups and calculates each group's share of that month's total. It ranks groups afresh each month. A tie is resolved alphabetically for the displayed names; this does not change CR2 or the gap. CR2 is the sum of the two highest shares. The gap is the highest share minus the second-highest share. Both use unrounded values.

The prepared CSV contains `date` (first day of the month, ISO format), `airline` (source brand), `ownership_group` (study grouping), and `passengers` (integer passenger journeys). ASK and RPK are not used or altered in this first preparation step.

## Other fields and limits

The file also contains passenger-kilometres, seat-kilometres, load factors and freight measures. Passenger-km and seat-km are reported in thousands. There are positive-passenger records with zero passenger-km/seat-km for Air Odisha in September 2018 and Air Deccan in March 2020; capacity analyses will need to document their treatment.

This file has no airline-by-route breakdown, fares or marginal costs. National concentration measures cannot establish route passenger shares, pricing power or consumer harm.
