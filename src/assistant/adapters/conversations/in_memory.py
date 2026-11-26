"""Adaptateur du port ConversationRegistry : un compteur de conversations par utilisateur, en mémoire vive."""


class InMemoryConversations:
    def __init__(self) -> None:
        self._counters: dict[str, int] = {}

    def current(self, user_id: str) -> str:
        return f"{user_id}#{self._counters.get(user_id, 0)}"

    def start_new(self, user_id: str) -> None:
        self._counters[user_id] = self._counters.get(user_id, 0) + 1
