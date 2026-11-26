from pathlib import Path

from assistant.config.tickets_settings import TicketsSettings


def test_the_environment_chooses_where_the_tickets_database_is() -> None:
    settings = TicketsSettings.from_environment({"TICKETS_DB": "/tmp/tickets.db"})

    assert settings.database == Path("/tmp/tickets.db")
    assert settings.seed == Path("data/tickets.sql")
