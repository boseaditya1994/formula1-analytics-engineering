"""Jolpica pagination, bounded retries and conservative request pacing."""

import time
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

DATASETS = {
    "races": ("RaceTable", "Races", None),
    "results": ("RaceTable", "Races", "Results"),
    "qualifying": ("RaceTable", "Races", "QualifyingResults"),
    "sprint": ("RaceTable", "Races", "SprintResults"),
    "driverstandings": ("StandingsTable", "StandingsLists", "DriverStandings"),
    "constructorstandings": ("StandingsTable", "StandingsLists", "ConstructorStandings"),
}


class SourceError(ValueError):
    """An incomplete or invalid source partition must not be loaded."""


class JolpicaClient:
    def __init__(
        self,
        client: httpx.Client,
        *,
        interval: float = 8.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.client = client
        self.interval = interval
        self.sleep = sleep
        self.clock = clock
        self.last_request: float | None = None

    def _request(self, endpoint: str, offset: int) -> dict[str, Any]:
        for attempt in range(5):
            if self.last_request is not None:
                self.sleep(max(0, self.interval - (self.clock() - self.last_request)))
            self.last_request = self.clock()
            response = None
            try:
                response = self.client.get(endpoint, params={"limit": 100, "offset": offset})
                if response.status_code != 429 and response.status_code < 500:
                    response.raise_for_status()
                    body = response.json()
                    if not isinstance(body, dict) or not isinstance(body.get("MRData"), dict):
                        raise SourceError("Missing MRData object")
                    return body["MRData"]
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt == 4:
                    raise
            if attempt == 4:
                raise SourceError("Retry budget exhausted")
            delay = float(2**attempt)
            if response is not None and response.headers.get("Retry-After"):
                value = response.headers["Retry-After"]
                try:
                    delay = max(delay, float(value))
                except ValueError:
                    try:
                        delay = max(
                            delay,
                            (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds(),
                        )
                    except (TypeError, ValueError):
                        pass
            if delay > 300:
                raise SourceError("Server requested a long cooldown; retry this partition later")
            self.sleep(delay)
        raise AssertionError("Unreachable")

    def fetch(self, dataset: str, season: int, round_number: int | None = None) -> list[dict]:
        table, collection, nested = DATASETS[dataset]
        scope = f"{season}/" + (f"{round_number}/" if round_number is not None else "")
        endpoint = f"{scope}{dataset}/"
        records: list[dict] = []
        expected = None
        offset = 0
        while True:
            data = self._request(endpoint, offset)
            try:
                total, returned_offset = int(data["total"]), int(data["offset"])
                parents = data[table][collection]
            except (KeyError, TypeError, ValueError) as exc:
                raise SourceError("Invalid pagination envelope") from exc
            if not isinstance(parents, list) or total < 0 or returned_offset != offset:
                raise SourceError("Invalid pagination values")
            if expected is not None and expected != total:
                raise SourceError("Source total changed during pagination")
            expected = total
            page = []
            for parent in parents:
                if not isinstance(parent, dict):
                    raise SourceError("Invalid parent record")
                if nested is None:
                    page.append(parent)
                else:
                    children = parent.get(nested)
                    if not isinstance(children, list):
                        raise SourceError("Missing nested records")
                    context = {k: v for k, v in parent.items() if k != nested}
                    for child in children:
                        if not isinstance(child, dict):
                            raise SourceError("Invalid nested record")
                        page.append({"context": context, "record": child})
            if not page and offset < total:
                raise SourceError("Pagination ended before advertised total")
            records.extend(page)
            offset += len(page)
            if offset > total:
                raise SourceError("More records than advertised total")
            if offset == total:
                return records


def open_client() -> httpx.Client:
    return httpx.Client(
        base_url="https://api.jolpi.ca/ergast/f1/",
        headers={"User-Agent": "Formula1AnalyticsEngineering/0.1.0"},
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=False,
    )
