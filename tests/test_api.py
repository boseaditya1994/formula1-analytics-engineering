import httpx
import pytest

from f1_pipeline.api import JolpicaClient, SourceError
from f1_pipeline.records import prepare


def envelope(total, offset, drivers):
    return {
        "MRData": {
            "total": str(total),
            "offset": str(offset),
            "RaceTable": {
                "Races": [
                    {
                        "season": "2025",
                        "round": "1",
                        "Results": [
                            {"Driver": {"driverId": driver}, "points": "1"} for driver in drivers
                        ],
                    }
                ]
                if drivers
                else []
            },
        }
    }


def client_for(handler, sleeps=None):
    http = httpx.Client(base_url="https://example.test/", transport=httpx.MockTransport(handler))
    return JolpicaClient(
        http, interval=0, sleep=(sleeps.append if sleeps is not None else lambda _: None)
    )


def test_nested_pagination_uses_child_counts():
    offsets = []

    def handler(request):
        offset = int(request.url.params["offset"])
        offsets.append(offset)
        return httpx.Response(200, json=envelope(3, offset, ["a", "b"] if offset == 0 else ["c"]))

    rows = client_for(handler).fetch("results", 2025)
    assert offsets == [0, 2]
    assert len(prepare("results", 2025, rows)) == 3


def test_empty_response():
    assert (
        client_for(lambda _: httpx.Response(200, json=envelope(0, 0, []))).fetch("results", 2025)
        == []
    )


@pytest.mark.parametrize("status", [404, 401])
def test_nonretryable_http_errors(status):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status)

    with pytest.raises(httpx.HTTPStatusError):
        client_for(handler).fetch("results", 2025)
    assert len(calls) == 1


@pytest.mark.parametrize("status", [500, 503, 429])
def test_retry_then_success(status):
    calls, sleeps = [], []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(status, headers={"Retry-After": "3"})
        return httpx.Response(200, json=envelope(1, 0, ["a"]))

    assert len(client_for(handler, sleeps).fetch("results", 2025)) == 1
    assert 3 in sleeps


def test_retry_budget_is_bounded():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(500)

    with pytest.raises(SourceError, match="budget"):
        client_for(handler).fetch("results", 2025)
    assert len(calls) == 5


def test_timeout_retries_are_bounded():
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("mock", request=request)

    with pytest.raises(httpx.ReadTimeout):
        client_for(handler).fetch("results", 2025)
    assert len(calls) == 5


@pytest.mark.parametrize("body", [{}, {"MRData": []}, {"MRData": {"total": "bad"}}])
def test_malformed_response(body):
    with pytest.raises(SourceError):
        client_for(lambda _: httpx.Response(200, json=body)).fetch("results", 2025)


def test_premature_empty_page_is_failure():
    with pytest.raises(SourceError, match="ended"):
        client_for(lambda _: httpx.Response(200, json=envelope(2, 0, []))).fetch("results", 2025)


def test_changing_total_is_failure():
    def handler(request):
        offset = int(request.url.params["offset"])
        return httpx.Response(200, json=envelope(2 if offset == 0 else 3, offset, ["a"]))

    with pytest.raises(SourceError, match="changed"):
        client_for(handler).fetch("results", 2025)


def test_invalid_json():
    with pytest.raises(ValueError):
        client_for(lambda _: httpx.Response(200, text="not json")).fetch("results", 2025)


def test_pacing():
    now, delays = [0.0], []

    def sleep(seconds):
        delays.append(seconds)
        now[0] += seconds

    http = httpx.Client(
        base_url="https://example.test/",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=envelope(0, 0, []))),
    )
    client = JolpicaClient(http, sleep=sleep, clock=lambda: now[0])
    client.fetch("results", 2025)
    client.fetch("results", 2025)
    assert sum(delays) == 8.0


def test_reject_duplicate_source_keys():
    rows = [
        {"context": {"season": "2025", "round": "1"}, "record": {"Driver": {"driverId": "a"}}}
    ] * 2
    with pytest.raises(SourceError, match="Duplicate"):
        prepare("results", 2025, rows)


@pytest.mark.parametrize(
    "context", [{"season": "2024", "round": "1"}, {"season": "2025", "round": "0"}, {}]
)
def test_invalid_identity(context):
    with pytest.raises(SourceError):
        prepare("results", 2025, [{"context": context, "record": {"Driver": {"driverId": "a"}}}])


def test_canonical_hash_and_correction():
    a = {"season": "2025", "round": "1", "raceName": "Example"}
    b = dict(reversed(list(a.items())))
    original = prepare("races", 2025, [a])[0]
    assert original["payload_hash"] == prepare("races", 2025, [b])[0]["payload_hash"]
    b["raceName"] = "Corrected"
    changed = prepare("races", 2025, [b])[0]
    assert original["business_key"] == changed["business_key"]
    assert original["payload_hash"] != changed["payload_hash"]
