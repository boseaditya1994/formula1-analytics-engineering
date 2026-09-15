# ADR-001: Jolpica for historical race and championship data

Status: accepted.

## Context

The MVP needs a free source for race results, qualifying, sprint results and
championship progression. It does not need live telemetry.

## Options

- Jolpica's Ergast-compatible API: documented structured race/championship records.
- FastF1: useful for timing/telemetry, with additional dependencies and session data.

## Decision

Use Jolpica directly through httpx. Preserve source payloads in Snowflake VARIANT;
retain season, round and source driver/constructor IDs as business keys. Reuse
nested reference attributes rather than separately querying every reference endpoint.
Use round-specific standings, since season-level standings alone do not preserve
race-by-race progression. Sprint results remain a separate dataset.

## Consequences

The pipeline depends on a community API, its availability and changing rate limits.
Pagination and source completeness are checked at runtime. A request interval of
eight seconds leaves some headroom under the documented 500/hour unauthenticated
limit, but cannot reserve capacity against other clients sharing the IP.
FastF1 telemetry remains a separate enhancement.

References: [API documentation](https://github.com/jolpica/jolpica-f1/blob/main/docs/README.md)
and [limits](https://github.com/jolpica/jolpica-f1/blob/main/docs/rate_limits.md).
