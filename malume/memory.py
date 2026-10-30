"""Local long-term memory: facts about the user and conversation history, in SQLite."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS facts (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    role TEXT NOT NULL CHECK (role IN ('user', 'model')),
    text TEXT NOT NULL,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class Memory:
    def __init__(self, path: Path | str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript(SCHEMA)

    def add_fact(self, text: str) -> int:
        """Save a fact; saving the same fact again returns the existing id."""
        text = text.strip()
        row = self.db.execute("SELECT id FROM facts WHERE lower(text) = lower(?)", (text,)).fetchone()
        if row:
            return row[0]
        with self.db:
            return self.db.execute("INSERT INTO facts (text) VALUES (?)", (text,)).lastrowid

    def forget_fact(self, fact_id: int) -> bool:
        with self.db:
            return self.db.execute("DELETE FROM facts WHERE id = ?", (fact_id,)).rowcount > 0

    def facts(self) -> list[tuple[int, str]]:
        return self.db.execute("SELECT id, text FROM facts ORDER BY id").fetchall()

    def add_message(self, role: str, text: str) -> None:
        with self.db:
            self.db.execute("INSERT INTO messages (role, text) VALUES (?, ?)", (role, text))

    def recent_messages(self, limit: int = 20) -> list[tuple[str, str]]:
        rows = self.db.execute(
            "SELECT role, text FROM messages ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return rows[::-1]
