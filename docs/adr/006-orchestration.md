# ADR-006: GitHub Actions for daily orchestration

Status: accepted.

## Context

The project needs inexpensive, reproducible scheduled execution but does not need a
long-running orchestration platform for its bounded batch workload.

## Options

- Manual local execution only.
- GitHub Actions with repository secrets and a cron schedule.
- Dedicated orchestration infrastructure such as Airflow, Prefect or Dagster.

## Decision

Use GitHub Actions for CI and the daily ingestion/dbt pipeline. Authenticate with the
scoped `F1_PIPELINE_SVC` Snowflake service user and a key-pair secret, not a personal
password/Duo flow. Run CI on push/pull request and the daily job at 06:00 UTC with
manual dispatch retained for recovery.

## Consequences

The solution is low-cost and visible in the repository. GitHub Actions schedules are
not a real-time scheduler and can be delayed, so race-week work remains a bounded
separate workflow rather than streaming. Writer workflows require shared concurrency
before both are enabled.
