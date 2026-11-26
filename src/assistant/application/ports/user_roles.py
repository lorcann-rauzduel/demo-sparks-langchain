"""Le port des rôles : qui a le droit de faire quoi, décidé hors du modèle."""

from typing import Protocol

from assistant.domain.user import Role


class UserRoles(Protocol):
    def role_of(self, user_id: str) -> Role: ...
