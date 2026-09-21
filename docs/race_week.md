# Race-week refresh design

## Objective

Provide timely current-race updates without weakening the proven daily pipeline or
claiming live streaming. The implemented `race_week_pipeline.yml` refreshes only the
current season's active race and only data that the current marts support.

## Supported refreshes

| Session milestone | Refresh datasets | Intended cadence |
| --- | --- | --- |
| Qualifying published | qualifying | One targeted run, with an optional bounded retry for source publication delay |
| Sprint published, where scheduled | sprint, driver standings, constructor standings | One targeted run |
| Grand Prix results published | results, driver standings, constructor standings | One targeted run, then a final reconciliation refresh |
| Non-session race-week period | races schedule only | Daily pipeline remains authoritative |

The workflow does not ingest lap-level telemetry, practice data, live positions,
timing gaps, tyre data or pit-stop analysis. Those require a separately approved
source/model design.

## Trigger and safety model

- The workflow is manually dispatchable and runs twice an hour Friday through Sunday
  (UTC). It derives the active race from the published current-season schedule and
  only selects a race whose date is within the next two UTC days.
- It will use the same `F1_PIPELINE_SVC` key-pair authentication as the daily job.
- A shared GitHub Actions concurrency group will prevent overlap with the daily
  workflow and the workflow will cancel neither an active daily pipeline nor a
  historical backfill.
- It will run targeted ingestion followed by the same dbt build/test gate as the
  daily workflow. Failure leaves audit evidence and returns a failed workflow.
- A source response with not-yet-published required results becomes observable
  `PENDING`, not a successful no-op.

## Freshness expectations

This is **near-real-time race-week ingestion**, not streaming. GitHub Actions
scheduling is limited to periodic execution and may be delayed under service load.
Jolpica data availability is also determined by the source. The dashboard is updated
only after its normal CSV export and manual Tableau Public republish.

## Acceptance criteria

Verified behaviour:

1. selects one current race and never rewrites historical seasons;
2. shares writer concurrency with the daily workflow;
3. records a successful or pending audit result for every selected partition;
4. runs dbt build/tests only when source data changes; and
5. exits successfully without a mart build outside the active-race window.

The local live verification on 2026-09-21 was a successful no-active-race no-op.
The workflow is documented in [daily_updates.md](daily_updates.md).
