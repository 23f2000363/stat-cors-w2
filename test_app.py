import re

from fastapi.testclient import TestClient

from main import ALLOWED_ORIGIN, EMAIL, app

client = TestClient(app)


def assert_metadata(response):
    assert response.headers.get("x-request-id")
    assert re.fullmatch(r"[0-9a-fA-F-]{36}", response.headers["x-request-id"])
    assert re.fullmatch(r"\d+(?:\.\d+)?", response.headers["x-process-time"])
    assert float(response.headers["x-process-time"]) >= 0


def test_stats_computed_from_supplied_values():
    response = client.get("/stats?values=-5,2,10,7")
    assert response.status_code == 200
    assert response.json() == {
        "email": EMAIL,
        "count": 4,
        "sum": 14,
        "min": -5,
        "max": 10,
        "mean": 3.5,
    }
    assert_metadata(response)


def test_allowed_preflight():
    response = client.options(
        "/stats",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
    assert_metadata(response)


def test_disallowed_preflight_has_no_allow_origin():
    response = client.options(
        "/stats",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code >= 400
    assert "access-control-allow-origin" not in response.headers
    assert_metadata(response)


def test_disallowed_simple_request_has_no_allow_origin():
    response = client.get("/stats?values=1,2,3", headers={"Origin": "https://evil.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
    assert_metadata(response)


def test_bad_input_is_rejected_and_has_metadata():
    response = client.get("/stats?values=1,nope,3")
    assert response.status_code == 400
    assert_metadata(response)


def test_each_request_has_unique_request_id():
    first = client.get("/health")
    second = client.get("/health")
    assert first.headers["x-request-id"] != second.headers["x-request-id"]
    assert_metadata(first)
    assert_metadata(second)
