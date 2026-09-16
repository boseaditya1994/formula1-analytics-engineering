# Dashboard

## Tool choice: Tableau Public Desktop

Tableau Public Desktop over Power BI Desktop, on this Windows machine, because Tableau
Public is designed for free, no-login public hosting with a shareable profile link —
the standard recruiter-facing choice for a portfolio project. Power BI's free-tier
"Publish to Web" requires a Microsoft account and is a weaker public-sharing story for
this use case. Neither tool was installed at the time this decision was made; the user
installed Tableau Public Desktop manually (GUI installs and dashboard authoring are
outside this session's automation reach — no desktop-control tool is available here).

## Known limitation: extract-only, no live Snowflake connection

Tableau Public Desktop cannot authenticate to a private Snowflake account — it only
works with data extracts (`.hyper`) or flat files, by design, since published
workbooks are public. This means:

- The dashboard cannot show a live Snowflake connection or refresh itself against the
  warehouse automatically.
- `scripts/export_dashboard_data.py` queries the marts and writes CSV extracts locally.
  Those CSVs are the actual data Tableau loads.
- "Daily refresh" for this dashboard means re-running the export script and
  republishing the workbook — not an automatic pull. This is an honest limitation of
  the free tool choice, not a gap in the pipeline itself (Snowflake marts refresh
  daily via GitHub Actions regardless; only the published Tableau Public workbook
  needs a manual republish to reflect that).

## Data export

```bash
uv run --frozen python scripts/export_dashboard_data.py --profile-file "$HOME/.dbt/profiles.yml"
```

Reads with the `F1_BI_READER` role (`snowflake/setup/02_roles.sql`) — SELECT-only on
`F1_ANALYTICS.MARTS`, granted to a user via:

```sql
grant role F1_BI_READER to user <user>;
```

Writes three CSVs to `dashboards/tableau/data/` (gitignored, regenerated on demand):

- `driver_race_performance.csv` — one row per driver per race, with circuit and
  country, grid/finish positions, points, status. Grain: driver × race.
- `driver_championship_progression.csv` — one row per driver per race, championship
  position/points after that race, and race-over-race deltas. Grain: driver × race.
- `constructor_championship_progression.csv` — the same shape at constructor grain.

Verified live against Snowflake: 787 / 809 / 394 rows respectively, columns and values
spot-checked (e.g. Lando Norris, McLaren, Albert Park Grand Prix Circuit for the 2025
season opener).

## Dashboard pages (planned)

Scoped to what the exported data actually supports — no page requires a metric the
marts don't have:

1. **Driver Championship** — points/position progression by season, filterable by
   driver and season, from `driver_championship_progression.csv`.
2. **Constructor Championship** — same, from `constructor_championship_progression.csv`.
3. **Race Analysis** — grid vs. finish, positions gained/lost, DNFs, by race and
   circuit, from `driver_race_performance.csv`.
4. **Circuit Analysis** — performance by circuit/country, from the same file's
   `circuit_name`/`country` columns.

Pages such as pit-stop analytics or lap-time trends are intentionally out of scope:
the current marts don't include `fct_lap_times`/`fct_pit_stops`, and this doc will not
claim a page that isn't backed by real data.

## Status

Data export pipeline built and verified. Workbook authoring in Tableau Public Desktop
is a manual, GUI-driven step — not yet done as of this writing.
