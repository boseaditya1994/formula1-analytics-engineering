# ADR-008: Manual Tableau Public extract republish

Status: accepted.

## Context

Snowflake marts refresh daily through GitHub Actions, while Tableau Public is an
extract-based companion BI delivery channel for this project. The React dashboard uses
the same controlled data-export boundary, but its public extract publication is pending.

## Decision

Keep Snowflake refresh automated and make the Tableau Public refresh an explicit
operator step: run `scripts/export_dashboard_data.py`, open the workbook with the new
CSV extracts, and republish it.

## Consequences

Warehouse analytics remain current daily. The Tableau companion artifact can lag until
its next manual republish; this is disclosed rather than described as automatic
dashboard refresh. React is implemented with an approved static-export design; its
future automated publication requires an approved data-delivery and hosting workflow.
Automating Tableau publication would
require a separately approved tool, credential model and review of Tableau Public
capabilities and terms.
