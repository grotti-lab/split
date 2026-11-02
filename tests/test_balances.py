from split import balances


def expense(amount, payer, shares):
    return {"amount": amount, "payer": payer, "shares": shares}


def test_one_expense():
    e = expense(3000, "Ana", [("Ana", 1000), ("Ben", 1000), ("Chloé", 1000)])
    b = balances.balances(["Ana", "Ben", "Chloé"], [e])
    assert b == {"Ana": 2000, "Ben": -1000, "Chloé": -1000}
    assert sum(b.values()) == 0


def test_no_expenses_is_all_zero():
    assert balances.balances(["Ana", "Ben"], []) == {"Ana": 0, "Ben": 0}


def test_text():
    assert balances.net_text(2000) == "is owed 20.00"
    assert balances.net_text(-1000) == "owes 10.00"
    assert balances.net_text(0) == "is settled up"


def test_suggested_payments_simple():
    b = {"Ana": 2000, "Ben": -1000, "Chloé": -1000}
    assert balances.suggested_payments(b) == [("Ben", "Ana", 1000), ("Chloé", "Ana", 1000)]


def test_suggested_payments_none_when_settled():
    assert balances.suggested_payments({"Ana": 0, "Ben": 0}) == []


def test_suggested_payments_biggest_first_and_fewest():
    b = {"Ana": 500, "Ben": -700, "Chloé": 300, "Dan": -100}
    p = balances.suggested_payments(b)
    assert p == [("Ben", "Ana", 500), ("Ben", "Chloé", 200), ("Dan", "Chloé", 100)]
    assert len(p) <= len(b) - 1


def test_suggested_payments_ties_by_member_order():
    b = {"Ana": 1000, "Ben": 1000, "Chloé": -1000, "Dan": -1000}
    assert balances.suggested_payments(b) == [("Chloé", "Ana", 1000), ("Dan", "Ben", 1000)]


def test_suggested_payments_settle_everyone():
    b = {"A": 333, "B": -111, "C": -222, "D": 5, "E": -5}
    left = dict(b)
    for d, c, cents in balances.suggested_payments(b):
        assert cents > 0 and isinstance(cents, int)
        left[d] += cents
        left[c] -= cents
    assert set(left.values()) == {0}


def test_payment_text():
    assert balances.payment_text(("Ben", "Ana", 1000)) == "Ben pays Ana 10.00"
