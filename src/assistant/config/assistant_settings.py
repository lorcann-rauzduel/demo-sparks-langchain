"""Les réglages du cas d'usage : les règles appliquées avant d'appeler le modèle."""

from collections.abc import Mapping
from dataclasses import dataclass

from assistant.config.environment import read_setting

DEFAULT_MAX_QUESTION_LENGTH = 2000


@dataclass(frozen=True)
class AssistantSettings:
    max_question_length: int
    support_users: frozenset[str]  # les identifiants qui ont le rôle support, par exemple discord:123

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> "AssistantSettings":
        return cls(
            max_question_length=int(
                read_setting(environment, "MAX_QUESTION_LENGTH", DEFAULT_MAX_QUESTION_LENGTH)
            ),
            support_users=frozenset(
                user.strip()
                for user in read_setting(environment, "SUPPORT_USERS", "").split(",")
                if user.strip()
            ),
        )
