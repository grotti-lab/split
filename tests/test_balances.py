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
