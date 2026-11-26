"""Le contexte d'exécution de l'agent : fourni par le code à chaque appel, jamais par le modèle."""

from dataclasses import dataclass

from assistant.domain.user import Role, User


@dataclass(frozen=True)
class AgentContext:
    user_id: str
    role: Role

    @classmethod
    def of(cls, user: User) -> "AgentContext":
        return cls(user.id, user.role)
