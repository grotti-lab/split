"""Shared fixtures, and the record of golden-set results that make report sends to Mycelium."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from split.app import create_app

REPORT = Path(__file__).parent.parent / ".reports" / "golden.json"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "split.db"))


def pytest_bdd_apply_tag(tag: str, function: object) -> bool:
    # Mycelium's tags (feature:, owner:, area:, test:) are metadata, not pytest marks.
    return True


def pytest_configure(config: pytest.Config) -> None:
    config._golden = []  # type: ignore[attr-defined]


SCENARIO = pytest.StashKey[tuple[str, str]]()


def pytest_bdd_before_scenario(request: pytest.FixtureRequest, feature: object, scenario: object) -> None:
    request.node.stash[SCENARIO] = (Path(feature.filename).name, scenario.name)  # type: ignore[attr-defined]


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> pytest.TestReport:
    report = yield
    found = item.stash.get(SCENARIO, None)
    if found and report.when == "call":
        details = call.excinfo.exconly()[:300] if call.excinfo else ""
        item.config._golden.append(  # type: ignore[attr-defined]
            {"feature_file": found[0], "scenario": found[1], "result": "pass" if report.passed else "fail", "details": details}
        )
    return report


def pytest_sessionfinish(session: pytest.Session) -> None:
    results = getattr(session.config, "_golden", [])
    if results:
        REPORT.parent.mkdir(exist_ok=True)
        REPORT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
