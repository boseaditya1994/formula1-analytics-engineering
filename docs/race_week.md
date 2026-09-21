# Race-week refresh design

## Objective

Provide timely current-race updates without weakening the proven daily pipeline or
claiming live streaming. The planned `race_week_pipeline.yml` will refresh only the
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

- The workflow will use `workflow_dispatch` for an operator-controlled target round
  and scheduled event windows for the current race once their UTC timing has been
  reliably derived from the published calendar.
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

Before enabling the workflow, verify that it:

1. selects one current race and never rewrites historical seasons;
2. respects shared workflow concurrency;
3. records a successful or pending audit result for every selected partition;
4. passes dbt build/tests after a successful source refresh;
5. leaves the existing daily schedule unchanged; and
6. is documented in [daily_updates.md](daily_updates.md).
