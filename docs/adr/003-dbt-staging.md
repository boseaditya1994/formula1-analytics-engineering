# ADR-003: dbt staging over a single VARIANT RAW table

Status: accepted.

The ingestion layer preserves source payloads in one auditable VARIANT table. dbt
staging provides a stable typed contract and filters only supported datasets;
dataset-specific parsing and dimensional models belong downstream. This keeps the
loader source-faithful while allowing SQL models to evolve independently.
