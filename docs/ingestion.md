# Historical ingestion

## Run from the repository root

Use the existing environment-based credentials (see `.env.example`), or explicitly
pass a local dbt profile containing exactly one Snowflake output. Profile values
are never copied into this repository or logged. Jinja templates in a profile are
not resolved: use environment variables instead. The ingestion connection always
selects F1_INGESTOR and disables secondary roles; it never falls back to an admin role.

```powershell
uv run --frozen f1-pipeline backfill --start-season 2025 --end-season 2025 --round 1 --datasets results
uv run --frozen f1-pipeline backfill --start-season 2025 --end-season 2025
uv run --frozen f1-pipeline backfill --start-season 2018 --end-season 2025
```

For the existing personal profile, append
`--profile-file "$HOME/.dbt/profiles.yml"`. This path is optional and local-only.

An omitted end season defaults to the last completed calendar year. Explicitly
request the current season when needed. `--round` requires a single season.
`--datasets` can select races, results, qualifying, sprint, driverstandings and
constructorstandings. The last two are fetched separately after each past race;
using only the season endpoint would lose championship progression history.

Driver, constructor and circuit attributes are preserved in nested source payloads.
Separate reference tables will be derived by dbt rather than fetching redundant
reference endpoints. Race results and sprint results are distinct datasets.

## Partition contract

| Dataset | Business key | Request / reconciliation partition |
| --- | --- | --- |
| races | season:round | season or one round |
| results, qualifying, sprint | season:round:driverId | season or one round |
| driverstandings | season:round:driverId | one round |
| constructorstandings | season:round:constructorId | one round |

The RAW key is `(dataset, business_key)`. SOURCE_RECORDS holds the latest observed
source payload, its SHA-256 hash, first-ingested timestamp, last-change timestamp,
and the run that inserted/changed it. It is not a full archive of earlier payload versions.
Numeric source strings are retained for dbt casting.

Before loading, pagination must match the advertised total and requested offset.
Changed totals, malformed keys, mismatched seasons/rounds and duplicate source keys
fail the partition. Identical duplicate keys also fail rather than hiding a pagination
problem. Empty historical partitions fail except sprint (not every season/race has one).

## Transaction and recovery

Each partition starts an audit row. MERGE inserts new keys and updates changed hashes;
unchanged records keep their timestamps and run ID. Within the same transaction,
the complete partition count and every source hash must reconcile with RAW before
the success audit commits. A mismatch rolls back the merge. Source deletions are not
silently applied; a retained unexpected key fails reconciliation for investigation.

Failures are recorded with a sanitized exception class and cause a nonzero CLI exit.
Raw connector messages and credential values are never printed. If the connection
is lost or the process is killed, a RUNNING audit entry can remain; investigate it
before a restart. Repeating a completed partition is safe. A partially completed
multi-season command can be resumed by selecting the remaining seasons/datasets.
Pass `--resume` to skip closed-season partitions whose latest audit attempt succeeded.
Omit it when deliberately refreshing historical corrections. Current-season partitions
are never skipped by this flag. See [daily updates](daily_updates.md) for bounded
correction refresh, missing-partition recovery and daily audit controls.

The local file lock prevents concurrent writers in this checkout. It is not a
distributed lock. Do not run another checkout/host against these RAW tables at the
same time; the planned GitHub Actions workflow must enforce shared concurrency.
Snowflake standard-table uniqueness is checked by the loader, not enforced by a PK.

## Source limits

The client uses `limit=100`, an identifying User-Agent and at least 8 seconds between
requests (at most about 450/hour per process). Timeout/network errors, 429 and 5xx
are retried at most five attempts. Retry-After is respected up to a 300-second
cooldown; longer cooldowns fail safely for a later retry. Other HTTP errors fail
immediately. Other clients on a shared IP can consume the same service quota.

Source documentation checked during implementation:
[endpoints](https://github.com/jolpica/jolpica-f1/blob/main/docs/README.md),
[rate limits](https://github.com/jolpica/jolpica-f1/blob/main/docs/rate_limits.md).

## Validation

`uv run --frozen python -m pytest -q` runs mocked HTTP, normalization, rollback,
reconciliation and CLI tests without cloud credentials. Live one-race, repeated-load
and season-backfill results are tracked separately in implementation_status.md.
This phase does not claim a dbt transformation, daily scheduler or dashboard.
