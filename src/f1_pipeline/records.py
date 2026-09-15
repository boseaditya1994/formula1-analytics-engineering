"""Normalize source partitions without discarding the source fields."""

import hashlib
import json
from typing import Any

from f1_pipeline.api import SourceError


def prepare(
    dataset: str, season: int, rows: list[dict], round_number: int | None = None
) -> list[dict]:
    output = []
    keys: dict[str, str] = {}
    for payload in rows:
        context = payload if dataset == "races" else payload.get("context", {})
        record = payload if dataset == "races" else payload.get("record", {})
        try:
            year, race = int(context["season"]), int(context["round"])
            if year != season or race < 1 or (round_number is not None and race != round_number):
                raise SourceError("Record outside requested partition")
            parts = [str(year), str(race)]
            if dataset != "races":
                entity = "Constructor" if dataset == "constructorstandings" else "Driver"
                field = "constructorId" if entity == "Constructor" else "driverId"
                identifier = record[entity][field]
                if not isinstance(identifier, str) or not identifier or ":" in identifier:
                    raise SourceError("Invalid source identifier")
                parts.append(identifier)
        except (KeyError, TypeError, ValueError) as exc:
            raise SourceError("Invalid record identity") from exc
        key = ":".join(parts)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode()).hexdigest()
        if key in keys:
            raise SourceError("Duplicate business key in source partition")
        keys[key] = digest
        output.append(
            {
                "business_key": key,
                "season": year,
                "round_number": race,
                "payload_hash": digest,
                "payload": payload,
            }
        )
    return output


def encode(records: list[dict[str, Any]]) -> str:
    return json.dumps(records, separators=(",", ":"), allow_nan=False)
