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


@given(parsers.parse('a group "{name}" with members {members}'))
def existing_group(client, groups, name, members):
    r = client.post("/groups", data={"name": name, "members": ",".join(split_names(members))})
    assert r.status_code == 200
    groups[name] = str(r.url)


@when(parsers.parse("someone adds {name} to the group"))
def add_member(client, groups, name):
    link = list(groups.values())[-1]
    r = client.post(link + "/members", data={"name": name})
    assert r.status_code == 200


@then(parsers.parse('the group "{name}" has the members {members}'))
def group_has_members(client, groups, name, members):
    page = client.get(groups[name]).text
    assert re.findall(r"<li>(.*?)</li>", page) == split_names(members)


@pytest.fixture
def last() -> dict:
    """The last response a scenario's action got, for steps that check what the person saw."""
    return {}


@when(parsers.parse("someone adds another member called {name}"))
def add_duplicate_member(client, groups, last, name):
    link = list(groups.values())[-1]
    last["response"] = client.post(link + "/members", data={"name": name})


@then(parsers.parse('they see the message "{message}"'))
def see_message(last, message):
    import html

    assert message in html.unescape(last["response"].text)
