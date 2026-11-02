from split.money import format_amount, parse_amount, split_equally


def test_parse_and_format():
    assert parse_amount("30.00") == 3000
    assert parse_amount("0.5") == 50
    assert parse_amount("7") == 700
    assert format_amount(334) == "3.34"
    assert format_amount(5) == "0.05"


def test_payer_sharing_takes_the_leftover():
    assert split_equally(1000, ["Ana", "Ben", "Chloé"], "Ana") == {"Ana": 334, "Ben": 333, "Chloé": 333}
    assert split_equally(1000, ["Ana", "Ben", "Chloé"], "Ben") == {"Ana": 333, "Ben": 334, "Chloé": 333}


def test_payer_not_sharing_first_person_takes_the_leftover():
    shares = split_equally(1000, ["Ben", "Chloé", "Dan"], "Ana")
    assert shares == {"Ben": 334, "Chloé": 333, "Dan": 333}
    assert sum(shares.values()) == 1000
