"""Les réglages de la base métier : où est la base, et le script qui la crée."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from assistant.config.environment import read_setting

DEFAULT_TICKETS_DB = "data/tickets.db"
DEFAULT_TICKETS_SEED = "data/tickets.sql"


@dataclass(frozen=True)
class TicketsSettings:
    database: Path
    seed: Path  # rejoué seulement si la base n'existe pas

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> "TicketsSettings":
        return cls(
            database=Path(read_setting(environment, "TICKETS_DB", DEFAULT_TICKETS_DB)),
            seed=Path(read_setting(environment, "TICKETS_SEED", DEFAULT_TICKETS_SEED)),
        )
