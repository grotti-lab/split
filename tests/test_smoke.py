"""The scaffold works: the app starts and serves its pages."""

from fastapi.testclient import TestClient


def test_home_page_loads(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "Split" in r.text


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"ok": True}
