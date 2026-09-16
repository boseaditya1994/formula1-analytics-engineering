# Daily updates

Run from the repository root using the locked Python environment:

```powershell
# Ingest, reconcile RAW, then build and test the marts. A failure stops the pipeline.
uv run --frozen python scripts/daily_pipeline.py --profile-file "$HOME/.dbt/profiles.yml"

# Ingestion only
uv run --frozen python -m f1_pipeline daily --profile-file "$HOME/.dbt/profiles.yml"

# Historical expansion; resume only skips successful closed-season partitions.
uv run --frozen python -m f1_pipeline backfill --start-season 2018 --end-season 2024 --resume --profile-file "$HOME/.dbt/profiles.yml"
uv run --frozen python -m f1_pipeline backfill --start-season 2026 --end-season 2026 --profile-file "$HOME/.dbt/profiles.yml"
```

The Python module entry point works where Windows Application Control blocks the
generated `f1-pipeline` launcher. Credentials are read from the existing profile or
environment; they are never stored in source files. COMPUTE_WH is unchanged.

Interactive password login can require a fresh Duo approval per connection. The
ingestion connector allows 180 seconds for login/socket operations so a short socket
timeout does not prematurely abandon MFA. Snowsight has a separate browser session;
its successful login does not authenticate Python or dbt. Repeated manual retries
can create additional pushes. MFA token caching and unattended authentication are
not configured. Scheduled execution will require an approved noninteractive
authentication design; extending the timeout does not make Duo unattended.

## Selection and correction policy

- Refresh the current season's complete schedule once per invocation, including future races.
- After the race date has passed in UTC, fetch missing results, qualifying and both
  championship snapshots. Fetch sprint results only when the schedule lists a Sprint.
- Recheck the latest two past races plus all races in the trailing 14 days.
  `--lookback-days` accepts 1–90 days.
- Include the preceding calendar season while that lookback crosses New Year.
- Skip older covered partitions; retry ones whose latest audited attempt was not
  successful. Previously committed RAW rows provide coverage for season-wide backfills.

This intentionally publishes weekend data no earlier than the UTC day after the
race. An empty required partition becomes PENDING, advances no successful checkpoint,
and returns exit code 2. Later invocations retry the gap. Source removals or changed
keys fail count reconciliation and require investigation; no automatic deletion occurs.
Corrections outside the active window require an explicit targeted backfill.

## Audit, recovery and freshness

INGESTION_RUNS is the durable per-partition control table. Success is committed in
the same transaction as the RAW MERGE and reconciliation. Control queries derive
the most recent attempt and last success; round 0 represents a season-wide request.
DAILY_RUNS records each ingestion invocation, its totals and final SUCCESS, PENDING
or FAILED status. This is ingestion status, not a claim that downstream dbt succeeded.

The pipeline wrapper runs dbt only after successful ingestion and propagates its
failure exit code. A failed build can be retried with `scripts/run_dbt.py build`.
Per-partition commits survive a later failure; re-running ingestion is idempotent.
A killed process can leave RUNNING audit records, which remain visible as incomplete.

`snowflake/monitoring/daily_health.sql` reports attempts, incomplete partitions and a
36-hour ingestion freshness threshold. It uses successful polling timestamps rather
than RAW UPDATED_AT, which changes only when source content changes.

Local locks prevent overlapping ingestion in one checkout and overlapping daily
pipeline wrappers. They do not coordinate other hosts or direct dbt commands: use
one writer and do not run a backfill while a daily pipeline is running. Remote
orchestration must add a shared concurrency group.

## Deployment status

This command implements daily update behavior. No scheduler is activated by these
files. GitHub Actions scheduling, secrets setup and deployment are the separate
automation milestone; Tableau Public refresh remains manual. See
implementation_status.md for actual live validation and outstanding blockers.
