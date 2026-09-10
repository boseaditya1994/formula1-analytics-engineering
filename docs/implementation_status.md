# Implementation status

Architecture approved: Python 3.12, Jolpica, Snowflake, dbt Core/Snowflake,
and Tableau Public with manual publication refresh.

- Phase 0: feasibility reviewed and architecture approved.
- Phase 1: bootstrap verified: Python 3.12.13, dbt Core 1.12.4,
  dbt-snowflake 1.12.0, connector 4.7.3; Ruff passed and two CLI tests passed.
- Phase 2 infrastructure: F1_ANALYTICS and RAW, STAGING, INTERMEDIATE, MARTS,
  AUDIT created and verified. All 30 statements in 02_roles.sql succeeded.
  Existing and future grants inspected for F1_INGESTOR, F1_TRANSFORMER and
  F1_BI_READER. User selected existing COMPUTE_WH; no warehouse was created or altered.
  Observed warehouse settings: X-Small, suspended, auto-suspend 60 seconds,
  auto-resume enabled. Role assignment and runtime role tests remain pending.
- Phases 3–8: ingestion, dbt, dimensional marts and quality pending.
- Phase 9: Tableau dashboard pending.
- Phases 10–11: orchestration and operational verification pending.
- Phases 12–14: final documentation, publication and portfolio material pending.

Snowflake connectivity, project resource creation and role grants have executed. Ingestion,
dashboard and scheduled runs remain unimplemented. GitHub CLI and Tableau
installation remain pending. No user or parent-role assignments were made.

Windows application control blocked the pytest launcher; use
`uv run --frozen python -m pytest`. The managed sandbox needs elevated access to
the existing uv Python directory and cache; this does not indicate a project test failure.

## Decisions

Reuse Python 3.12 in a local virtual environment. Commit uv.lock and use frozen
installations. Invoke dbt through uv to avoid the global Fusion preview.
Preserve existing user-level profiles. Start with 2018 onward schedules, reference
entities, race/sprint results, qualifying and official standings. Defer lap and
pit-stop ingestion. Revisit recent race weekends daily and support targeted repair.

Discover Snowflake authentication and privileges before provisioning. Account/security
changes require approval of concrete SQL. Public GitHub publication requires separate
approval; preserve existing origin. Never expose credentials in output.
