"""Money is integer cents everywhere, never floats."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


def parse_amount(text: str) -> int:
    """'30.00' -> 3000. Raises ValueError for anything that isn't a plain amount with at most two decimals."""
    text = text.strip()
    if not re.fullmatch(r"\d+([.,]\d{1,2})?", text):
        raise ValueError(f"Not an amount: {text!r}")
    try:
        return int((Decimal(text.replace(",", ".")) * 100).to_integral_exact())
    except InvalidOperation as e:  # pragma: no cover
        raise ValueError(f"Not an amount: {text!r}") from e


def format_amount(cents: int) -> str:
    """3000 -> '30.00'"""
    sign = "-" if cents < 0 else ""
    return f"{sign}{abs(cents) // 100}.{abs(cents) % 100:02d}"


def split_equally(total: int, sharing: list[str], payer: str) -> dict[str, int]:
    """Split total cents among the people sharing.

    Leftover cents go one each: the payer first if they are sharing, then the others in listed order.
    Shares always add up to the total.
    """
    if not sharing:
        raise ValueError("Nobody to share with")
    base, extra = divmod(total, len(sharing))
    order = ([payer] if payer in sharing else []) + [m for m in sharing if m != payer]
    shares = {m: base for m in sharing}
    for m in order[:extra]:
        shares[m] += 1
    return shares
