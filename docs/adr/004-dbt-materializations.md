# ADR-004: dbt materializations for the first marts

Status: accepted.

Small reusable reference dimensions are tables. Race, qualifying, sprint and
championship snapshot facts use incremental MERGE with dataset-specific unique keys.
An inclusive source updated_at watermark includes newly observed corrections to old
races. RAW timestamps indicate ingestion changes, not race-event dates. Staging is a
view; championship progression tables recompute their small window-function results
so that a corrected earlier snapshot also updates subsequent deltas.

Dimension attributes are selected from one deterministic latest source row. No SCD2
claim is made. The custom schema macro maps to the explicitly provisioned STAGING
and MARTS schemas; this single-environment choice must be adapted before shared CI.
