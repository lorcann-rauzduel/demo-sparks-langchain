from pathlib import Path

from assistant.adapters.tickets.sqlite_tickets import SqliteTickets

SEED = Path("data/tickets.sql")


def test_a_ticket_is_read_from_the_database_created_from_the_seed(tmp_path: Path) -> None:
    tickets = SqliteTickets.open(tmp_path / "tickets.db", SEED)

    assert tickets.status(4) == "Ticket 4: Laptop stolen, open, priority high."


def test_an_unknown_ticket_has_no_status(tmp_path: Path) -> None:
    tickets = SqliteTickets.open(tmp_path / "tickets.db", SEED)

    assert tickets.status(99) is None


def test_closing_a_ticket_changes_its_status(tmp_path: Path) -> None:
    tickets = SqliteTickets.open(tmp_path / "tickets.db", SEED)

    assert tickets.close(2) is True
    assert tickets.status(2) == "Ticket 2: Printer offline on floor 2, closed, priority low."


def test_an_unknown_ticket_cannot_be_closed(tmp_path: Path) -> None:
    assert SqliteTickets.open(tmp_path / "tickets.db", SEED).close(99) is False
