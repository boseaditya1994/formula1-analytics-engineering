You are operating my Windows desktop to build a Tableau Public Desktop dashboard for a
portfolio project called the Formula 1 Analytics Engineering Platform. Work
incrementally: build one tab/sheet, show me the result, wait for confirmation, then
move to the next. Do not publish anything publicly without showing me first and
getting my explicit go-ahead.

## Design reference

Model the structure on "Formula 1 Racing" by Pratheek PJ on Tableau Public
(https://public.tableau.com/app/profile/pratheek.pj/viz/Formula1Racing_20190909_v2/F1_Championship2019-Monitor),
a 5-tab workbook: (1) Championship Monitor — standings table + circuit map + track
info card, (2) Technical Analysis — engine/tyre/pit-stop specs, (3) The Champs Behind
The Wheel — driver photo grid + bio + performance stats, (4) Team Detail Analysis —
team logo grid + history + budget/income/employees, (5) Who Won When — driver
dropdown + season/circuit results table.

We are matching the exploratory, 5-tab spirit — not the exact content. Our data is
real, live-ingested race results and standings (via the Jolpica API), not the
bio/financial/technical datasets that dashboard drew on. Specifically we have NO
driver photos, age, nationality, or date of birth; NO engine, tyre, or pit-stop data;
NO team budget, income, or employee counts; NO track-diagram geometry or lap records.
Do not invent, estimate, or backfill any of that — every tab below is redesigned to
use only the columns listed in "Data available." Where the reference dashboard's tab
can't be honestly reproduced (Technical Analysis, and the bio/financial panels on
tabs 3–4), it is replaced with something adjacent built from real columns, not faked
or left as a placeholder.

## Data available

Tableau Public Desktop cannot connect live to Snowflake (extract-only by design,
since published workbooks are public). The data has already been exported to three
CSVs on disk at:

D:\Projects\formula1-analytics-engineering\dashboards\tableau\data\

- **driver_race_performance.csv** (787 rows) — grain: one row per driver per race.
  Columns: RESULT_KEY, SEASON, ROUND_NUMBER, RACE_NAME, DRIVER_ID, DRIVER_CODE,
  DRIVER_NAME, CONSTRUCTOR_ID, CONSTRUCTOR_NAME, FINISHING_POSITION, GRID_POSITION,
  POSITIONS_LOST, POSITIONS_GAINED, POINTS, LAPS_COMPLETED, STATUS, FASTEST_LAP_RANK,
  UPDATED_AT, CIRCUIT_NAME, COUNTRY

- **driver_championship_progression.csv** (809 rows) — grain: one row per driver per
  race, showing championship state after that race.
  Columns: RACE_KEY, DRIVER_ID, STANDING_KEY, SEASON, ROUND_NUMBER,
  CHAMPIONSHIP_POSITION, CHAMPIONSHIP_POINTS, WINS, UPDATED_AT,
  CHAMPIONSHIP_POSITION_TEXT, DRIVER_NAME, RACE_NAME, POINTS_CHANGE,
  CHAMPIONSHIP_POSITIONS_GAINED

- **constructor_championship_progression.csv** (394 rows) — same shape as above, at
  constructor grain instead of driver.
  Columns: RACE_KEY, CONSTRUCTOR_ID, STANDING_KEY, SEASON, ROUND_NUMBER,
  CHAMPIONSHIP_POSITION, CHAMPIONSHIP_POINTS, WINS, UPDATED_AT, CONSTRUCTOR_NAME,
  RACE_NAME, POINTS_CHANGE, CHAMPIONSHIP_POSITIONS_GAINED

Data covers real, live-ingested Formula 1 seasons (via the Jolpica API), not sample or
synthetic data. Only build visuals that these columns genuinely support — do not
invent metrics like lap times, pit stops, or driver salaries; those datasets don't
exist in this export. There is no latitude/longitude column, but Tableau can
geocode COUNTRY automatically as a built-in geographic role — use that for the map,
don't fabricate coordinates.

## Tabs to build (in this order)

**Tab 1 — Championship Monitor** (mirrors the reference's tab 1, minus track specs we
don't have)
Connect to driver_championship_progression.csv, filtered to the last ROUND_NUMBER per
SEASON (the final standings). Left: table of CHAMPIONSHIP_POSITION, DRIVER_NAME,
CONSTRUCTOR_NAME (bring in from driver_race_performance.csv via DRIVER_ID + SEASON),
CHAMPIONSHIP_POINTS, WINS — like the reference's "2019 Standings" list. Right: a
world map using driver_race_performance.csv's COUNTRY column with Tableau's built-in
geographic role (no lat/long needed), one mark per circuit, sized by race count —
like the reference's "Grand Prix Circuit" map. Do not attempt to reproduce the
reference's track-diagram image or its Track Info card (circuit length, lap record,
etc.) — those fields don't exist in our export; skip them rather than inventing
plausible-looking numbers. Add a SEASON filter (single-value dropdown).

**Tab 2 — Race Analysis** (replaces the reference's Technical Analysis tab, which
needs engine/tyre/pit-stop data we don't have)
Connect to driver_race_performance.csv. Main chart: scatter or slope comparing
GRID_POSITION vs FINISHING_POSITION per driver per race, colored by
POSITIONS_GAINED (diverging color: gains positive, losses negative) — this is our
honest equivalent of "who over/under-performed," using real data instead of engine
specs. Add a small multiple or bar showing STATUS breakdown (Finished vs each DNF
reason) per SEASON. Filters: SEASON, RACE_NAME.

**Tab 3 — Champs Behind The Wheel** (driver deep-dive, same intent as the reference's
tab 3, without the photo/bio panel we can't back with real data)
Connect to driver_race_performance.csv and driver_championship_progression.csv. Add
a DRIVER_NAME parameter or filter styled as a selector (grid of names, since we have
no driver photos to grid instead). For the selected driver: a line of
CHAMPIONSHIP_POINTS by ROUND_NUMBER (points progression), a line/step chart of
CHAMPIONSHIP_POSITION by ROUND_NUMBER (race standings over the season), and three KPI
numbers computed from driver_race_performance.csv: races entered (row count), podiums
(count where FINISHING_POSITION <= 3), wins (count where FINISHING_POSITION = 1). Do
not add age, nationality, date of birth, or a photo — we have no such columns. Add a
SEASON filter.

**Tab 4 — Team Detail Analysis** (constructor deep-dive, same intent as the
reference's tab 4, without the budget/income/employee panel we can't back with real
data)
Connect to constructor_championship_progression.csv. Add a CONSTRUCTOR_NAME selector.
For the selected constructor: a line of CHAMPIONSHIP_POINTS by ROUND_NUMBER across
SEASON (team history), and KPI numbers for wins and podium finishes derived the same
way as Tab 3 but at constructor grain using driver_race_performance.csv's
CONSTRUCTOR_NAME. Do not add budget, income, sponsor, or employee figures — those
aren't in our data and would have to be invented.

**Tab 5 — Who Won When**
Connect to driver_race_performance.csv, filtered to FINISHING_POSITION = 1. Left: a
line of CHAMPIONSHIP_POINTS-equivalent (or POINTS scored per race) over ROUND_NUMBER
for a selected DRIVER_NAME (dropdown), like the reference's "Player Performance"
chart. Right: a table of SEASON, ROUND_NUMBER, RACE_NAME, DRIVER_NAME,
CONSTRUCTOR_NAME, CIRCUIT_NAME, COUNTRY, POINTS — one row per race win, filterable by
SEASON — like the reference's "Season Wise Results." This tab is the closest match to
the reference dashboard since it needs nothing beyond race results.

## Rules

- Show me each tab after building it before moving to the next.
- Do not publish to Tableau Public (or anywhere) without showing me the finished
  workbook first and getting explicit confirmation.
- Do not invent, assume, or backfill data that isn't in these three CSVs — skip any
  part of the reference dashboard (e.g. technical/telemetry analysis) that these
  columns can't support, and tell me you're skipping it rather than faking it.
- If a step requires an application, menu, or button you can't find or operate,
  stop and tell me exactly what's blocking you rather than skipping or faking it.
