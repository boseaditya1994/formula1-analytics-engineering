# Implementation status

Last verified: 2026-09-21. Python 3.12.13, dbt Core 1.12.4, dbt-snowflake 1.12.0,
Snowflake connector 4.7.3 and existing COMPUTE_WH.

## Verified in Snowflake

F1_ANALYTICS and RAW/STAGING/INTERMEDIATE/MARTS/AUDIT exist. The approved
F1_INGESTOR and F1_TRANSFORMER assignments were applied and both roles were tested.
Project grants are installed. Shared warehouse settings were not changed.

The 2025 backfill completed while an earlier response reported its state as unknown.
RAW and audit queries on September 15 established the actual result:

| Dataset | RAW rows | Distinct business keys | Rounds |
| --- | ---: | ---: | ---: |
| races | 24 | 24 | 24 |
| results | 479 | 479 | 24 |
| qualifying | 479 | 479 | 24 |
| sprint | 120 | 120 | 6 |
| driverstandings | 498 | 498 | 24 |
| constructorstandings | 240 | 240 | 24 |
| Total | 1,840 | — | — |

All 54 recorded ingestion runs were SUCCESS. The first-race load inserted 20
records; its rerun inserted/updated zero and reported 20 unchanged. Other seasons
and the current season have not been backfilled.

An authenticated dbt Core build completed with **15 models and 88 passing data tests**,
zero failures, in 59.34 seconds. Invocation: 76e4a418-51dc-4ba1-9124-3faff302c8e5.

- One STAGING source view.
- Six dimensions: driver, constructor, circuit, race, season and date.
- Five incremental facts: race results, qualifying, sprint results, driver standings
  and constructor standings.
- Three analytical tables: race performance and driver/constructor championship progression.

Tests cover fields, keys, relationships, RAW-to-fact counts, mart reconciliation,
grid movement and source-backed rank nullability. The earlier Snowflake connection
errors no longer reproduce; no specific root cause was confirmed. The project uses
the locked Core runtime and one thread. Python's 28-test suite and Ruff passed at
the preceding checkpoint; this change modifies SQL and its dbt tests.

An unchanged-source incremental rebuild also passed all 88 tests and rebuilt all
15 models in 65.67 seconds. Invocation: c63ba4d7-2c91-457d-bd90-c9c0f8ff3dcf.
Before/after row counts, distinct keys and HASH_AGG content fingerprints matched
for every fact:

| Fact | Rows | Distinct keys |
| --- | ---: | ---: |
| Race results | 479 | 479 |
| Qualifying results | 479 | 479 |
| Sprint results | 120 | 120 |
| Driver standings | 498 | 498 |
| Constructor standings | 240 | 240 |

The local evidence is in ignored artifacts/incremental_verification.json.

## Source-data correction

The first expanded build failed because seven driver-standing snapshots had null
numeric position and positionText='-'. Six occurred at round 1 and one at round 2
of 2025. The fact now preserves championship_position_text. Null numeric ranks
are allowed only with the explicit '-' source marker; other invalid ranks fail.
The new column was added and backfilled using MERGE with reprocess_history=true;
no table drop or fabricated numeric ranking was used.

## Resume

Run from the repository root:

```powershell
uv run --frozen python scripts/run_dbt.py build --profile-file "$HOME/.dbt/profiles.yml"
uv run --frozen python scripts/verify_incremental.py --profile-file "$HOME/.dbt/profiles.yml"
```

The second command compares all five fact row counts, unique keys and content
fingerprints before/after an unchanged-source build. Its report is written only
after verification passes. This verification succeeded on September 16, 2026.

## Remaining milestones

- Historical expansion for 2018–2024.
- Broader quality/audit reporting and analytics refinements.
- Tableau Public refresh automation beyond the documented manual export-and-republish
  process available on the free/extract-only workflow.
- Portfolio screenshots, résumé and LinkedIn material.

Personal credentials/profiles stay unmodified and out of Git. The ignored local
dbt profile contains environment references only.

## Expansion and daily updates checkpoint (2026-09-16)

The requested 2018–2024 expansion was attempted but each backfill command failed
at Snowflake login, before loading a new partition. A separate connection check
succeeded once, but subsequent ingestion attempts again failed. The final diagnostic
identified OperationalError 250001, caused by 251011 and a socket ReadTimeout during
login. No account/security or warehouse configuration was changed. Both Snowflake's
web endpoint and Jolpica were reachable. Live API validation found 21 schedule rows
for 2018 and 23 for 2026; this is source validation, not proof of a RAW backfill.

After the user confirmed Snowsight SELECT 1 succeeds, the connector returned a
different error twice: DatabaseError 370001 (08001), "Failed to connect to DB:
Internal error", before initialization. One diagnostic included request ID
0979031b-11e9-4185-96b4-7375e6493a62. No root cause has been established; this is
not evidence of invalid credentials or missing project grants.

Implemented and locally verified:

- `backfill --resume` skips only successful closed-season partition checkpoints.
- `daily` refreshes schedules, missing past-race datasets, the latest two races,
  and a configurable correction window (14 days by default).
- Empty required datasets remain PENDING and do not advance success.
- DAILY_RUNS DDL and monitoring queries expose ingestion status and polling freshness.
- `scripts/daily_pipeline.py` builds/tests marts only after successful ingestion,
  and propagates ingestion or dbt failure to its caller.
- **41 Python tests passed**, Ruff passed, and git diff whitespace checks passed.

An initial diagnostic change set a 10-second socket timeout and 60-second login
window. The user subsequently reported repeatedly approving Duo pushes. Inspection
of the installed connector confirmed it applies the socket timeout while awaiting
Duo approval, making that short timeout unsuitable for interactive MFA. Both login
and socket timeouts have now been corrected to 180 seconds; the network retry window
remains 60 seconds (a retry window is not a hard request deadline). This correction
has now been verified with a fresh live MFA login: a manual `connect()` against the
dbt profile completed successfully after a single Duo approval. `ACCOUNT_USAGE.LOGIN_HISTORY`
showed the prior failures split into two distinct phases: repeated `EXT_AUTHN_DENIED`
(error 390120, no second factor recorded) consistent with the socket timeout abandoning
pending Duo approvals, followed by a run of `INTERNAL_ERROR` (error 370001) with no
Duo attempt recorded at all — most likely transient account-level throttling from the
rapid retry burst rather than a separate defect, since a clean login now succeeds
under the same code with no further changes. See Snowflake's
[timeout documentation](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect#managing-connection-timeouts).

`scripts/daily_pipeline.py` has now been run end to end against Snowflake: ingestion
succeeded across all 2026 partitions (races, results, qualifying, sprint, both
standings datasets), followed by a full dbt build and test — 5 incremental models,
9 table models, 1 view model, and 103/103 data tests passed (0 errors, 0 warnings),
including `championship_mart_reconciliation` and `reconcile_race_mart`.

## Automation and dashboard delivery (2026-09-21)

GitHub Actions now runs the daily pipeline at 06:00 UTC and supports manual
dispatch. It authenticates as the scoped `F1_PIPELINE_SVC` service user using
Snowflake key-pair authentication, so scheduled runs require no interactive Duo
approval. The workflow has completed successfully on consecutive scheduled runs from
September 17 through September 21, each performing ingestion followed by dbt build
and test. CI also passes on pushes, with Ruff and the 42-test Python suite green.

The Tableau Public workbook
`dashboards/tableau/F1_Analytics_Engineering_Platform.twb` is complete and [published](<https://public.tableau.com/views/F1_Analytics_Engineering_Platform/ChampionshipMonitor?:language=en-US&publish=yes&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link>). It delivers Championship Monitor, Champs Behind The Wheel, Race Analysis,
Race Winners and Team Detail Analysis dashboards from the exported analytics marts.
Tableau Public uses generated CSV extracts rather than a live Snowflake connection;
the warehouse refreshes daily, while the public workbook is refreshed by exporting
and manually republishing it. See [dashboard.md](dashboard.md) for the supported
fields and refresh process.

## Historical expansion and race-week refresh (2026-09-21)

The resumable 2018–2024 backfill completed successfully. Latest audit checkpoints are
all `SUCCESS`: 46 partitions for 2018, 46 for 2019, 38 for 2020, 48 for 2021, 48 for
2022, 48 for 2023 and 52 for 2024. A transient Jolpica `RemoteProtocolError` during
the first 2022 attempt was retried through `--resume`; no successful partition was
reloaded. RAW now contains 11,050 historical records and 11,050 distinct
dataset/business keys for these seasons.

A one-time dbt historical reprocess added `championship_position_text` to constructor
standings, preserving two source-provided unranked Haas snapshots (`positionText='-'`)
from 2018 and 2020 instead of fabricating numeric ranks. The subsequent Snowflake dbt
build completed with 15 models and 89 data tests: **104/104 passed**.

`.github/workflows/race_week_pipeline.yml` is now implemented. It runs twice hourly
Friday–Sunday UTC, is manually dispatchable, shares writer concurrency with the daily
pipeline, and refreshes only one imminent/current race's qualifying, sprint where
scheduled, results, and championship standings. Its local live check outside an
active race window completed successfully as a no-op; source publication remains
observable as `PENDING`. See [race_week.md](race_week.md).
