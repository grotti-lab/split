"""Balances: what each member is owed or owes, in cents.

A member's net = what they paid minus their shares of every expense.
Positive: owed money. Negative: owes. Zero: settled up.
"""

from __future__ import annotations

from . import money


def nets(members: list[str], expenses: list[dict]) -> dict[str, int]:
    """Member -> net cents, from expenses shaped like db.list_expenses (amount, payer, shares)."""
    net = {m: 0 for m in members}
    for e in expenses:
        net[e["payer"]] += e["amount"]
        for name, cents in e["shares"]:
            net[name] -= cents
    return net


def net_text(cents: int) -> str:
    return money.format_amount(cents)
