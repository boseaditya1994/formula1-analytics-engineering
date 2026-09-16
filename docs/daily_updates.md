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
Verified live: a manual login with a single Duo approval now succeeds; see
[implementation_status.md](implementation_status.md) for the LOGIN_HISTORY evidence.

### Unattended authentication for scheduled runs

Scheduled execution cannot approve an interactive Duo push, so it needs a separate,
non-interactive auth path rather than a longer timeout. `connection.py` already
supports this without code changes: `snowflake-connector-python` selects key-pair
authentication automatically when `private_key_file` (and optionally
`private_key_file_pwd`) is supplied instead of a password, via either
`SNOWFLAKE_PRIVATE_KEY_FILE` / `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` or the matching
profile fields.

Setup, verified live:

1. Generate an RSA key pair locally (never committed to the repo):
   ```bash
   openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
   openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
   ```
2. Create a dedicated service user in Snowflake — not a personal MFA-protected
   login — scoped to `F1_INGESTOR`, and register the public key:
   ```sql
   create user f1_pipeline_svc default_role = F1_INGESTOR default_warehouse = COMPUTE_WH;
   grant role F1_INGESTOR to user f1_pipeline_svc;
   alter user f1_pipeline_svc set rsa_public_key='<rsa_key.pub, header/footer stripped>';
   ```
3. Store the private key outside the repo (e.g. `~/.snowflake/f1_pipeline_svc.p8`)
   and point the pipeline at it:
   ```bash
   export SNOWFLAKE_ACCOUNT="<account>"
   export SNOWFLAKE_USER="F1_PIPELINE_SVC"
   export SNOWFLAKE_PRIVATE_KEY_FILE="$HOME/.snowflake/f1_pipeline_svc.p8"
   ```

A live login as `F1_PIPELINE_SVC` with these three variables set (no password, no
`SNOWFLAKE_AUTHENTICATOR` override) succeeded with zero prompts and no Duo push.

### GitHub Actions

`.github/workflows/daily_pipeline.yml` runs `scripts/daily_pipeline.py` on a daily
cron (06:00 UTC) and on manual dispatch. It authenticates as `F1_PIPELINE_SVC` using
key-pair auth end to end — `dbt`'s Snowflake profile also needed extending to accept
`private_key_path`/`private_key_passphrase` (see `scripts/run_dbt.py` and
`dbt_f1/profiles.yml.example`) since dbt previously required a password, which no
unattended runner can supply through Duo.

`.github/workflows/ci.yml` runs Ruff, the Python test suite, and an offline dbt parse
on every pull request and push to `main`; it needs no Snowflake credentials.

Required repository secrets for the daily workflow, set via `gh secret set` or the
GitHub UI (never committed):

- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER` — `F1_PIPELINE_SVC`
- `SNOWFLAKE_PRIVATE_KEY` — the contents of `rsa_key.p8`
- `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` — only if the key was generated with one (this
  project's key was generated unencrypted, so this can be left unset)

`F1_PIPELINE_SVC` also needs the `F1_TRANSFORMER` role granted in Snowflake so the
same key-pair credential covers both ingestion and dbt.

Verified live via `gh workflow run daily_pipeline.yml`: the first attempt failed in
under 2 seconds with a bare `ValueError`, too fast to be a real Snowflake round trip.
A temporary debug step confirmed the written key file was empty (`wc -l` returned 0)
even though `gh secret list` showed `SNOWFLAKE_PRIVATE_KEY` as set — the secret had
been set from an empty value. Re-setting it directly from the key file
(`gh secret set SNOWFLAKE_PRIVATE_KEY --body ...` reading the `.p8` file's exact bytes)
fixed it. The next run completed successfully in 2m44s: ingestion plus a full dbt
build and test, 103/103 tests passed, 0 errors, with zero Duo prompts throughout.

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
