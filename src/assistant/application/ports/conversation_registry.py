"""Le port des conversations : la conversation en cours de chaque utilisateur."""

from typing import Protocol


class ConversationRegistry(Protocol):
    def current(self, user_id: str) -> str: ...

    def start_new(self, user_id: str) -> None: ...
