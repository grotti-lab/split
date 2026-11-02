"""SQLite storage. Money is stored as whole cents.

The team adds tables as the features need them; SCHEMA_VERSION goes up with each change.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1
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
