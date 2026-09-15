# Implementation status

Last verified: 2026-09-15. Python 3.12.13, dbt Core 1.12.4, dbt-snowflake 1.12.0,
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

An authenticated dbt Core build completed with **8 models and 49 passing data tests**,
zero errors/warnings, in 60.45 seconds. Its model set:

- STAGING.stg_source_records
- MARTS.dim_driver (21 rows), dim_constructor (10), dim_circuit (24), dim_race (24)
- MARTS.fct_race_results (479) and fct_qualifying_results (479)
- MARTS.driver_race_performance (479)

The build exercised fields, keys, relationships, RAW-to-fact counts, race-mart
points/count reconciliation and business rules. Full incremental idempotency
verification remains pending.

## Current target and blocker

The project now parses with **15 models and 87 data tests**. Added models cover
season/date dimensions, sprint results, official championship standings and
championship progression. Their live build did not complete.

The expanded build encountered connection error 250001 while opening workers.
Reducing dbt to one thread produced Snowflake internal connection error
**370001 / SQLSTATE 08001**. Independent connector checks with both ingestion
and original-profile logins failed with the same code. This is separate from
the earlier Codex quota/Fusion issues. No confirmed account-specific cause or
regional incident has been established.

The eight-model build remains the last verified cloud result. Existing views may
have refreshed during the expanded attempt; the seven new models are not reported
as successfully deployed. Local checks passed: 28 Python tests, Ruff, and an offline
parse of the complete graph. The scripts use locked dbt Core, not global Fusion.

## Resume

Once Snowflake accepts connections, run from the repository root:

```powershell
uv run --frozen python scripts/run_dbt.py build --profile-file "$HOME/.dbt/profiles.yml"
uv run --frozen python scripts/verify_incremental.py --profile-file "$HOME/.dbt/profiles.yml"
```

The second command compares all five fact row counts, unique keys and content
fingerprints before/after an unchanged-source build. Its report is written only
after verification passes. That verification has not yet succeeded.

## Remaining milestones

- Expanded dbt build and incremental verification.
- Historical backfill for 2018–2024 and the current season.
- Phase 4 daily correction selection, checkpoints and ingestion freshness.
- Broader quality/audit reporting and analytics refinements.
- Tableau installation, dashboard and manual publication refresh.
- GitHub CLI, CI, scheduling, publication approval and portfolio material.

No daily scheduler, dashboard, public publication or résumé impact is claimed.
Personal credentials/profiles stay unmodified and out of Git. The ignored local
dbt profile contains environment references only.
