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


@when(parsers.parse("someone removes {name} from the group"))
def remove_member(client, groups, last, name):
    link = list(groups.values())[-1]
    last["response"] = client.post(link + "/members/remove", data={"name": name})


@then(parsers.parse('they see the message "{message}"'))
def see_message(last, message):
    import html

    assert message in html.unescape(last["response"].text)

# --- expenses -------------------------------------------------------------------------------

def parse_split(clause: str) -> dict:
    """The split clause of an expense step, as the form fields for it.

    "split equally", "split between X and Y", "for X only" and
    "split by amounts Ana 10.00, Ben 5.00" are built.
    """
    clause = clause.strip()
    if clause == "split equally":
        return {}
    if clause.startswith("split between "):
        return {"sharing": split_names(clause[len("split between "):])}
    if clause.startswith("split by amounts "):
        parts = [part.rsplit(" ", 1) for part in split_names(clause[len("split by amounts "):])]
        return {
            "split_mode": "amounts",
            "exact_member": [who for who, _ in parts],
            "exact_amount": [amount for _, amount in parts],
        }
    if clause.endswith(" only") and clause.startswith("for "):
        return {"sharing": [clause[4:-5].strip()]}
    raise NotImplementedError(f"split clause not built yet: {clause!r}")


def post_expense(client, groups, name, amount, payer, split):
    link = list(groups.values())[-1]
    data = {"description": name, "amount": amount, "payer": payer, **parse_split(split)}
    return client.post(link + "/expenses", data=data)


@when(parsers.parse('{who} adds an expense "{name}" of {amount} paid by {payer}, {split}'))
def add_expense(client, groups, last, who, name, amount, payer, split):
    last["response"] = post_expense(client, groups, name, amount, payer, split)


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


def expense_form_action(client, groups, name, suffix):
    """The action of the expense's form on the group page whose action ends with suffix."""
    page = client.get(list(groups.values())[-1]).text
    for block in re.findall(r'<div class="expense".*?</div>\s*</div>', page, re.S):
        if re.search(r'data-name="(.*?)"', block).group(1) == name:
            for action in re.findall(r'<form[^>]*action="(.*?)"', block):
                if action.endswith(suffix):
                    return action
    raise AssertionError(f"no expense {name!r} on the page")


@when(parsers.parse('someone changes the amount of "{name}" to {amount}'))
def change_amount(client, groups, last, name, amount):
    action = expense_form_action(client, groups, name, "/edit")
    last["response"] = client.post(action, data={"amount": amount})


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


@when(parsers.parse('someone deletes the expense "{name}"'))
def delete_expense(client, groups, name):
    action = expense_form_action(client, groups, name, "/delete")
    assert client.post(action).status_code == 200


# --- balances ----------------------------------------------------------------------------

def nets_on_page(client, groups) -> dict:
    """Member -> net as shown on the group page (text such as 'is owed 20.00')."""
    page = client.get(list(groups.values())[-1]).text
    return dict(re.findall(r'class="balance" data-member="[^"]*">(.*?) <span class="net">(.*?)</span>', page))


@then(parsers.parse("{name} is settled up"))
def settled_up(client, groups, name):
    assert nets_on_page(client, groups)[name] == "is settled up"


@then(parsers.parse("{name} is owed {amount}"))
def is_owed(client, groups, name, amount):
    assert nets_on_page(client, groups)[name] == f"is owed {amount}"


@then(parsers.re(r"(?P<name>\S+) owes (?P<amount>\d+\.\d\d)"))
def owes(client, groups, name, amount):
    assert nets_on_page(client, groups)[name] == f"owes {amount}"


def payments_on_page(client, groups) -> list:
    page = client.get(list(groups.values())[-1]).text
    return re.findall(r'<div class="payment">(.*?)</div>', page)


@then(parsers.parse("the suggested payments are {payments}"))
def suggested_payments_are(client, groups, payments):
    assert sorted(payments_on_page(client, groups)) == sorted(n.strip('"') for n in split_names(payments))


@then(parsers.parse('the only suggested payment is "{payment}"'))
def only_suggested_payment(client, groups, payment):
    assert payments_on_page(client, groups) == [payment]


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


# --- settle up ---------------------------------------------------------------------------

@when(parsers.parse("{who} records paying {to} {amount}"))
@given(parsers.parse("{who} recorded paying {to} {amount}"))
def records_payment(client, groups, last, who, to, amount):
    link = list(groups.values())[-1]
    last["response"] = client.post(link + "/payments", data={"payer": who, "payee": to, "amount": amount})


@then(parsers.parse('the group shows "{text}"'))
def group_shows(client, groups, text):
    import html

    assert text in html.unescape(client.get(list(groups.values())[-1]).text)
