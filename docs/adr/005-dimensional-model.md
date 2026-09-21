# ADR-005: Explicit race-grain star schema

Status: accepted.

## Context

RAW source records preserve nested, source-faithful payloads. Dashboard and analytical
queries need stable, typed tables with unambiguous grains instead of repeatedly
parsing JSON.

## Decision

Model driver, constructor, circuit, race, season and date dimensions. Model race,
qualifying and sprint facts at driver × event grain, and driver/constructor standings
at championship snapshot-after-round grain. Use source business identifiers and
document each fact's natural unique key.

No SCD Type 2 model is introduced: the source and current portfolio questions do not
justify historical dimension versions. Driver-to-constructor membership remains on
event facts because a driver can represent different constructors across a season.

## Consequences

The mart layer supports correct joins, incremental MERGE behaviour and Tableau
exports without invented surrogate keys. Users must not sum cumulative championship
points across rounds. Detailed grains and relationships are in
[data_model.md](../data_model.md).
