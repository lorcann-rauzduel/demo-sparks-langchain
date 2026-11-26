"""L'utilisateur, tel que le cœur le connaît : son identifiant et son rôle."""

from dataclasses import dataclass
from typing import Literal

Role = Literal["employee", "support"]


@dataclass(frozen=True)
class User:
    id: str
    role: Role
