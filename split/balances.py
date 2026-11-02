"""Balances: what each member is owed or owes, in cents.

A member's net = what they paid minus their shares of every expense.
Positive: owed money. Negative: owes. Zero: settled up.
"""

from __future__ import annotations

from . import money


def balances(members: list[str], expenses: list[dict], payments: list[dict] | None = None) -> dict[str, int]:
    """Member -> net cents, from expenses shaped like db.list_expenses (amount, payer, shares)
    and payments shaped like db.list_payments (from, to, amount): paying raises your net, receiving lowers it."""
    net = {m: 0 for m in members}
    for e in expenses:
        net[e["payer"]] += e["amount"]
        for name, cents in e["shares"]:
            net[name] -= cents
    for p in payments or []:
        net[p["from"]] += p["amount"]
        net[p["to"]] -= p["amount"]
    return net


def net_text(cents: int) -> str:
    """'is owed 20.00' / 'owes 10.00' / 'is settled up'"""
    if cents > 0:
        return f"is owed {money.format_amount(cents)}"
    if cents < 0:
        return f"owes {money.format_amount(-cents)}"
    return "is settled up"


def suggested_payments(balances: dict[str, int]) -> list[tuple[str, str, int]]:
    """(from, to, cents) payments that settle everyone: biggest debtor pays biggest creditor
    the smaller of the two amounts, repeat. Ties go to the earlier member (dict order)."""
    left = dict(balances)
    order = {m: i for i, m in enumerate(left)}
    payments = []
    while True:
        debtors = [m for m, c in left.items() if c < 0]
        creditors = [m for m, c in left.items() if c > 0]
        if not debtors or not creditors:
            return payments
        d = min(debtors, key=lambda m: (left[m], order[m]))
        c = max(creditors, key=lambda m: (left[m], -order[m]))
        cents = min(-left[d], left[c])
        payments.append((d, c, cents))
        left[d] += cents
        left[c] -= cents


def payment_text(payment: tuple[str, str, int]) -> str:
    """'Ben pays Ana 10.00'"""
    payer, payee, cents = payment
    return f"{payer} pays {payee} {money.format_amount(cents)}"
