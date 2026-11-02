"""SQLite storage. Money is stored as whole cents.

The team adds tables as the features need them; SCHEMA_VERSION goes up with each change.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 0
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
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
