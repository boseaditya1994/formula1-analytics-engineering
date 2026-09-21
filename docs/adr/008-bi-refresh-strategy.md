# ADR-008: Manual Tableau Public extract republish

Status: accepted.

## Context

Snowflake marts refresh daily through GitHub Actions, while Tableau Public is an
extract-based public delivery channel for this project.

## Decision

Keep Snowflake refresh automated and make the Tableau Public refresh an explicit
operator step: run `scripts/export_dashboard_data.py`, open the workbook with the new
CSV extracts, and republish it.

## Consequences

Warehouse analytics remain current daily. The public dashboard can lag until its next
manual republish; this is disclosed rather than described as automatic dashboard
refresh. Automating publication would require a separately approved tool, credential
model and review of Tableau Public capabilities and terms.
