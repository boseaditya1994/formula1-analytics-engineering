# ADR-007: Tableau Public as companion BI artifact

Status: accepted.

## Context

The project needs a publicly shareable dashboard on Windows without introducing paid
BI capacity or exposing the private Snowflake account.

## Decision

Use Tableau Public Desktop and publish the completed workbook to Tableau Public as a
companion BI artifact. Export approved MARTS data as CSV extracts for the workbook
rather than connecting Tableau Public to Snowflake. The separate React dashboard is
the primary polished portfolio experience and consumes only approved static exports.

## Consequences

The workbook is easy for recruiters to open and share, and demonstrates traditional
BI capability alongside the future React experience. It intentionally cannot show a
live private Snowflake connection, and refresh requires a new export plus manual
republish. The design is documented in [dashboard.md](../dashboard.md).
