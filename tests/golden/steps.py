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


# --- expenses -------------------------------------------------------------------------------

def parse_split(clause: str) -> dict:
    """The split clause of an expense step, as the form fields for it.

    "split equally" is built. Later tasks add "split between X and Y" and
    "split by amounts Ana 10.00, Ben 5.00" here, in this one place.
    """
    clause = clause.strip()
    if clause == "split equally":
        return {}
    raise NotImplementedError(f"split clause not built yet: {clause!r}")


def post_expense(client, groups, name, amount, payer, split):
    link = list(groups.values())[-1]
    data = {"description": name, "amount": amount, "payer": payer, **parse_split(split)}
    return client.post(link + "/expenses", data=data)


@when(parsers.parse('{who} adds an expense "{name}" of {amount} paid by {payer}, {split}'))
def add_expense(client, groups, who, name, amount, payer, split):
    post_expense(client, groups, name, amount, payer, split)


@given(parsers.parse('an expense "{name}" of {amount} paid by {payer}, {split}'))
def existing_expense(client, groups, name, amount, payer, split):
    assert post_expense(client, groups, name, amount, payer, split).status_code == 200


def expenses_on_page(client, groups) -> dict:
    """Expense name -> {'amount', 'payer', 'shares': {member: 'x.xx'}}, read off the group page."""
    page = client.get(list(groups.values())[-1]).text
    found = {}
    for block in re.findall(r'<div class="expense".*?</div>\s*</div>', page, re.S):
        name = re.search(r'data-name="(.*?)"', block).group(1)
        found[name] = {
            "amount": re.search(r'class="amount">(.*?)<', block).group(1),
            "payer": re.search(r'class="payer">(.*?)<', block).group(1),
            "shares": dict(re.findall(r'data-member="[^"]*">(.*?) (-?\d+\.\d\d)<', block)),
        }
    return found


@then(parsers.parse('the expense "{name}" shows {amount} paid by {payer}'))
def expense_shows(client, groups, name, amount, payer):
    e = expenses_on_page(client, groups)[name]
    assert (e["amount"], e["payer"]) == (amount, payer)


@then(parsers.parse('the shares of "{name}" are {shares}'))
def shares_are(client, groups, name, shares):
    expected = {}
    for part in split_names(shares):
        who, amount = part.rsplit(" ", 1)
        expected[who] = amount
    assert expenses_on_page(client, groups)[name]["shares"] == expected


@then("the group has no expenses")
def no_expenses(client, groups):
    assert expenses_on_page(client, groups) == {}


# --- sharing the link -----------------------------------------------------------------------

@pytest.fixture
def opened() -> dict:
    """The page a fresh visitor got from the group's link."""
    return {}


@when(parsers.parse("{who} opens the group's link"))
def opens_link(client, groups, opened):
    from fastapi.testclient import TestClient

    # a new client on the same app: no cookies, no session (there are no accounts)
    with TestClient(client.app) as fresh:
        r = fresh.get(list(groups.values())[-1])
    assert r.status_code == 200
    opened["page"] = r.text


@then(parsers.parse("{who} sees the members {members}"))
def sees_members(opened, who, members):
    assert re.findall(r"<li>(.*?)</li>", opened["page"]) == split_names(members)


@then(parsers.parse('{who} sees the expense "{name}" of {amount}'))
def sees_expense(opened, who, name, amount):
    pattern = rf'data-name="{re.escape(name)}".*?class="amount">{re.escape(amount)}<'
    assert re.search(pattern, opened["page"], re.S)
