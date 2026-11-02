"""Step definitions for the golden sets: the team's code behind the person's words.

Empty at the start. A scenario with a step that has no definition here fails with
"Step definition is not found": it's a use case the team hasn't built yet.
"""

import re

import pytest

from pytest_bdd import given, parsers, then, when

from split import db


def split_names(text: str) -> list[str]:
    """'Ana, Ben and Chloé' -> ['Ana', 'Ben', 'Chloé']"""
    return [n.strip() for n in re.split(r",|\band\b", text) if n.strip()]


@pytest.fixture
def groups() -> dict:
    """Group name -> the group's link, for the scenario's groups."""
    return {}


@given("no groups exist")
def no_groups(client):
    assert db.get_group(client.app.state.db_path, "none") is None  # fresh database per scenario


@when(parsers.parse('Ana creates a group "{name}" with members {members}'))
def create_group(client, groups, name, members):
    r = client.post("/groups", data={"name": name, "members": ",".join(split_names(members))})
    assert r.status_code == 200
    groups[name] = str(r.url)


@then(parsers.parse('the group "{name}" has the members {members}'))
def group_has_members(client, groups, name, members):
    page = client.get(groups[name]).text
    assert re.findall(r"<li>(.*?)</li>", page) == split_names(members)
