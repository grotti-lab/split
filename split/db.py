"""SQLite storage. Money is stored as whole cents.

The team adds tables as the features need them; SCHEMA_VERSION goes up with each change.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 3
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,  -- the group's link: /groups/<slug>
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    name TEXT NOT NULL,
    UNIQUE (group_id, name)
);
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    description TEXT NOT NULL,
    amount INTEGER NOT NULL,  -- whole cents
    payer_id INTEGER NOT NULL REFERENCES members(id)
);
CREATE TABLE IF NOT EXISTS expense_shares (
    expense_id INTEGER NOT NULL REFERENCES expenses(id),
    member_id INTEGER NOT NULL REFERENCES members(id),
    share INTEGER NOT NULL,  -- whole cents
    PRIMARY KEY (expense_id, member_id)
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    from_id INTEGER NOT NULL REFERENCES members(id),
    to_id INTEGER NOT NULL REFERENCES members(id),
    amount INTEGER NOT NULL  -- whole cents
);
"""


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init(path: Path) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)", (str(SCHEMA_VERSION),))


def create_group(path: Path, slug: str, name: str, members: list[str]) -> None:
    with connect(path) as conn:
        cur = conn.execute("INSERT INTO groups(slug, name) VALUES(?, ?)", (slug, name))
        conn.executemany("INSERT INTO members(group_id, name) VALUES(?, ?)", [(cur.lastrowid, m) for m in members])


def get_group(path: Path, slug: str) -> dict | None:
    with connect(path) as conn:
        g = conn.execute("SELECT id, slug, name FROM groups WHERE slug = ?", (slug,)).fetchone()
        if g is None:
            return None
        rows = conn.execute("SELECT name FROM members WHERE group_id = ? ORDER BY id", (g["id"],)).fetchall()
        return {"slug": g["slug"], "name": g["name"], "members": [r["name"] for r in rows]}


def add_member(path: Path, slug: str, name: str) -> bool:
    """Add a member to a group. False if the group doesn't exist."""
    with connect(path) as conn:
        g = conn.execute("SELECT id FROM groups WHERE slug = ?", (slug,)).fetchone()
        if g is None:
            return False
        conn.execute("INSERT INTO members(group_id, name) VALUES(?, ?)", (g["id"], name))
        return True


def add_expense(path: Path, slug: str, description: str, amount: int, payer: str, shares: dict[str, int]) -> bool:
    """Record an expense; shares maps member name -> cents. False if the group doesn't exist."""
    with connect(path) as conn:
        g = conn.execute("SELECT id FROM groups WHERE slug = ?", (slug,)).fetchone()
        if g is None:
            return False
        ids = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM members WHERE group_id = ?", (g["id"],))}
        cur = conn.execute(
            "INSERT INTO expenses(group_id, description, amount, payer_id) VALUES(?, ?, ?, ?)",
            (g["id"], description, amount, ids[payer]),
        )
        conn.executemany(
            "INSERT INTO expense_shares(expense_id, member_id, share) VALUES(?, ?, ?)",
            [(cur.lastrowid, ids[m], c) for m, c in shares.items()],
        )
        return True


def list_expenses(path: Path, slug: str) -> list[dict]:
    """The group's expenses, oldest first, each with amount, payer and a share (cents) for every member."""
    with connect(path) as conn:
        g = conn.execute("SELECT id FROM groups WHERE slug = ?", (slug,)).fetchone()
        if g is None:
            return []
        members = conn.execute("SELECT id, name FROM members WHERE group_id = ? ORDER BY id", (g["id"],)).fetchall()
        out = []
        for e in conn.execute(
            "SELECT e.id, e.description, e.amount, m.name AS payer FROM expenses e "
            "JOIN members m ON m.id = e.payer_id WHERE e.group_id = ? ORDER BY e.id", (g["id"],)
        ).fetchall():
            got = {r["member_id"]: r["share"] for r in conn.execute(
                "SELECT member_id, share FROM expense_shares WHERE expense_id = ?", (e["id"],))}
            out.append({
                "id": e["id"], "description": e["description"], "amount": e["amount"], "payer": e["payer"],
                "shares": [(m["name"], got.get(m["id"], 0)) for m in members],
            })
        return out


def remove_member(path: Path, slug: str, name: str) -> str:
    """Remove a member. "removed", "has_expenses" (paid or has a share: kept) or "missing"."""
    with connect(path) as conn:
        m = conn.execute(
            "SELECT m.id FROM members m JOIN groups g ON g.id = m.group_id WHERE g.slug = ? AND m.name = ?",
            (slug, name),
        ).fetchone()
        if m is None:
            return "missing"
        used = conn.execute(
            "SELECT 1 FROM expenses WHERE payer_id = ?1 UNION SELECT 1 FROM expense_shares WHERE member_id = ?1",
            (m["id"],),
        ).fetchone()
        if used:
            return "has_expenses"
        conn.execute("DELETE FROM members WHERE id = ?", (m["id"],))
        return "removed"


def delete_expense(path: Path, slug: str, expense_id: int) -> bool:
    """Delete an expense and its shares. False if the group or expense doesn't exist."""
    with connect(path) as conn:
        row = conn.execute(
            "SELECT e.id FROM expenses e JOIN groups g ON g.id = e.group_id WHERE g.slug = ? AND e.id = ?",
            (slug, expense_id),
        ).fetchone()
        if row is None:
            return False
        conn.execute("DELETE FROM expense_shares WHERE expense_id = ?", (expense_id,))
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return True


def add_payment(path: Path, slug: str, payer: str, payee: str, amount: int) -> bool:
    """Record that payer paid payee (cents). False if the group or a member doesn't exist."""
    with connect(path) as conn:
        g = conn.execute("SELECT id FROM groups WHERE slug = ?", (slug,)).fetchone()
        if g is None:
            return False
        ids = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM members WHERE group_id = ?", (g["id"],))}
        if payer not in ids or payee not in ids:
            return False
        conn.execute(
            "INSERT INTO payments(group_id, from_id, to_id, amount) VALUES(?, ?, ?, ?)",
            (g["id"], ids[payer], ids[payee], amount),
        )
        return True


def list_payments(path: Path, slug: str) -> list[dict]:
    """The group's payments, oldest first: {id, from, to, amount}."""
    with connect(path) as conn:
        return [dict(r) for r in conn.execute(
            "SELECT p.id, f.name AS \"from\", t.name AS \"to\", p.amount FROM payments p "
            "JOIN groups g ON g.id = p.group_id JOIN members f ON f.id = p.from_id "
            "JOIN members t ON t.id = p.to_id WHERE g.slug = ? ORDER BY p.id", (slug,))]


def delete_payment(path: Path, slug: str, payment_id: int) -> bool:
    """Remove a recorded payment of this group. False if there is no such payment."""
    with connect(path) as conn:
        cur = conn.execute(
            "DELETE FROM payments WHERE id = ? AND group_id = (SELECT id FROM groups WHERE slug = ?)",
            (payment_id, slug))
        return cur.rowcount > 0
