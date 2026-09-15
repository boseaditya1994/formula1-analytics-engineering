# dbt development and verification

Run from the project root using the locked Python environment. The global dbt
command is a separate Fusion preview; it is not the runtime used by these scripts.

```powershell
uv run --frozen python scripts/run_dbt.py parse --offline
uv run --frozen python scripts/run_dbt.py build --profile-file "$HOME/.dbt/profiles.yml"
uv run --frozen python scripts/verify_incremental.py --profile-file "$HOME/.dbt/profiles.yml"
```

The runner reads exactly one Snowflake output from the explicitly supplied local
credential profile. It does not modify that file. Account/user/password are injected
into DBT_ENV_SECRET variables, which dbt masks in logs. The ignored project profile
contains environment references only and is copied from profiles.yml.example if
missing. Without --profile-file, the runner reads SNOWFLAKE_ACCOUNT,
SNOWFLAKE_USER and SNOWFLAKE_PASSWORD from the environment or local .env.
The dbt runner currently supports password authentication; ingestion separately
supports its documented alternate authentication fields. Unattended key-pair
configuration is a future orchestration task.

F1_TRANSFORMER and COMPUTE_WH are fixed in the single-thread project profile. Model pre-hooks
disable secondary roles. The SQL assignments in snowflake/setup were explicitly
approved and executed; creating a new user's role assignment still requires approval.
No warehouse settings are changed by dbt.

Run artifacts and compiled SQL are in ignored dbt_f1/target and logs. The incremental
verification report is in ignored artifacts/incremental_verification.json. A failed
dbt command returns a nonzero exit code. A build includes both models and data tests;
a separate unconditional dbt test step is unnecessary.

An offline parse checks Jinja, the dependency graph and configuration. It does not
prove Snowflake SQL validity. An authenticated build and reconciliation establish
that separately. See implementation_status.md for measured results and remaining work.
