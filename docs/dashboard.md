# Dashboard delivery

## Product positioning

The project uses two complementary dashboard surfaces:

- **React interactive dashboard (primary showcase):** the implemented polished,
  responsive `dashboards/react` application. It reads curated MARTS data through an
  approved public/static export and is live on [GitHub Pages](https://boseaditya1994.github.io/formula1-analytics-engineering/).
- **Tableau Public (published companion BI artifact):** the verified workbook that
  demonstrates conventional BI delivery, exploratory analysis, and public sharing.

React must never connect from the browser directly to Snowflake or expose Snowflake
credentials. Tableau remains an intentional companion artifact rather than being
described as the future primary visual experience.

## React static-export delivery

The React app retrieves three public CSV files from `/data/` at runtime. The export
script is the only path that accesses Snowflake and always uses the scoped,
SELECT-only `F1_BI_READER` role. Generate both Tableau and React extracts with:

```powershell
uv run --frozen python scripts/export_dashboard_data.py --react-out-dir dashboards/react/public/data
```

The generated React files are gitignored. They are public presentation data and must
be reviewed before a dashboard deployment; no Snowflake credential, private key, or
profile is copied into the React project or browser bundle.

## Automated public delivery

`.github/workflows/publish_dashboard.yml` runs after a successful Daily pipeline or
Race-week pipeline run, and can be manually dispatched. It regenerates the public
extracts using the service user's private key only on the GitHub-hosted runner, builds
the static React export, and deploys `dist/client` to GitHub Pages. The deployed
artifact contains only browser assets and the three approved CSV extracts.

## Delivered companion workbook

The finished Tableau Public workbook is [F1_Analytics_Engineering_Platform.twb](../dashboards/tableau/F1_Analytics_Engineering_Platform.twb) and is published on [Tableau Public](<https://public.tableau.com/views/F1_Analytics_Engineering_Platform/ChampionshipMonitor?:language=en-US&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link>). It contains five interactive dashboards backed only by the exported mart fields:

1. **Championship Monitor** — driver standings, championship progression, race points and key driver KPIs.
2. **Champs Behind The Wheel** — driver-focused season progression and race-by-race performance.
3. **Race Analysis** — grid versus finish, points, finishing status and circuit context.
4. **Race Winners** — race-level winners and points across the selected season.
5. **Team Detail Analysis** — constructor comparison, team points history, wins and podium KPIs.

No telemetry, lap-time or pit-stop metrics are claimed: those entities are not in the current marts.

## Why Tableau Public remains included

Tableau Public Desktop was selected over Power BI because it provides free public hosting with a shareable portfolio workbook. The workbook was authored and published manually in Tableau Public Desktop.

## Extract-only refresh model

Tableau Public cannot use a live connection to the private Snowflake account. It consumes local CSV extracts instead:

- `scripts/export_dashboard_data.py` reads SELECT-only from `F1_ANALYTICS.MARTS` using `F1_BI_READER`.
- The script writes the three CSV extracts consumed by Tableau to `dashboards/tableau/data/`.
- GitHub Actions refreshes Snowflake ingestion and marts daily at 06:00 UTC.
- To refresh the published dashboard, rerun the export and manually republish the Tableau workbook. This is an intentional, documented free-tier limitation.

## Data export

```powershell
uv run --frozen python scripts/export_dashboard_data.py
```

The export contains:

- `driver_race_performance.csv` — driver × race; grid/finish, points, status, circuit and country.
- `driver_championship_progression.csv` — driver × race; championship position/points and deltas.
- `constructor_championship_progression.csv` — constructor × race; championship position/points and deltas.

The exports were verified live against Snowflake: 787, 809 and 394 rows respectively. The files are intentionally gitignored and regenerated on demand.

## Security

`F1_BI_READER` is a SELECT-only role on `F1_ANALYTICS.MARTS`. Grant it to an authorised export user with:

```sql
grant role F1_BI_READER to user <user>;
```
