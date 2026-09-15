# ADR-002: Atomic partition loads with current-state RAW records

Status: accepted for the initial backfill.

## Context

Historical API payloads may be corrected. A failed download must not publish a
partial season or advance a successful-load record. Repeated loads must be safe.

## Options

- Append every downloaded record: duplicates would require downstream resolution.
- Replace entire tables: excessive scope and potential data loss.
- MERGE each completely validated source partition: bounded, repeatable writes.

## Decision

Use `(dataset, business_key)` as the RAW identity and a canonical JSON SHA-256
hash to detect changes. Fetch and validate a complete request partition before
opening a data transaction. MERGE, count/hash reconciliation and successful audit
update commit atomically. Fail the partition if unexpected retained rows exist;
do not automatically delete source records.

Each partition receives its own audit run ID. A process-level lock prevents local
overlap; only one host is supported until orchestration adds a concurrency group.

## Consequences

Repeated loads of unchanged data produce no RAW inserts or updates. Failed runs
retain a failure audit when the database is reachable. Source payloads are preserved
in current-state RAW, but prior payload versions are not archived in this phase.
The payload list is held in memory and bound as JSON; this suits race-level data,
not full telemetry. Large telemetry ingestion would need staged files/chunking.
Persisted automatic checkpoint selection is deferred to daily ingestion.
