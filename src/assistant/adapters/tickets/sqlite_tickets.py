"""La base métier : les tickets du support, dans SQLite."""

import sqlite3
from pathlib import Path


class SqliteTickets:
    def __init__(self, database: Path) -> None:
        self._database = database

    @classmethod
    def open(cls, database: Path, seed: Path) -> "SqliteTickets":
        """Ouvre la base, créée depuis le script SQL au premier lancement."""
        if not database.exists():
            database.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(database) as connection:
                connection.executescript(seed.read_text(encoding="utf-8"))
        return cls(database)

    def status(self, ticket_id: int) -> str | None:
        # mode=ro : la lecture ne peut rien modifier, même si la requête le demandait
        with sqlite3.connect(f"file:{self._database}?mode=ro", uri=True) as connection:
            row = connection.execute(
                "SELECT title, status, priority FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
        return f"Ticket {ticket_id}: {row[0]}, {row[1]}, priority {row[2]}." if row else None

    def close(self, ticket_id: int) -> bool:
        """Ferme un ticket ; False s'il n'existe pas."""
        with sqlite3.connect(self._database) as connection:
            updated = connection.execute("UPDATE tickets SET status = 'closed' WHERE id = ?", (ticket_id,))
        return updated.rowcount == 1
