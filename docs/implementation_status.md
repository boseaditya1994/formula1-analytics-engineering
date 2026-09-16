# Implementation status

Last verified: 2026-09-16. Python 3.12.13, dbt Core 1.12.4, dbt-snowflake 1.12.0,
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

- Historical backfill for 2018–2024 and the current season.
- Phase 4 daily correction selection, checkpoints and ingestion freshness.
- Broader quality/audit reporting and analytics refinements.
- Tableau installation, dashboard and manual publication refresh.
- GitHub CLI, CI, scheduling, publication approval and portfolio material.

No daily scheduler, dashboard, public publication or résumé impact is claimed.
Personal credentials/profiles stay unmodified and out of Git. The ignored local
dbt profile contains environment references only.
