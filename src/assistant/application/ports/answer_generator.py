"""Le port de génération : produire la réponse à une question, dans une conversation donnée."""

from collections.abc import Iterator
from typing import Protocol

from assistant.domain.answer import ActionToApprove, Answer, Token
from assistant.domain.user import User


class AnswerGenerator(Protocol):
    """L'utilisateur accompagne chaque appel : sa mémoire long terme le suit, son rôle borne ses outils."""

    def generate(self, conversation_id: str, user: User, question: str) -> Answer | ActionToApprove: ...

    def stream(
        self, conversation_id: str, user: User, question: str
    ) -> Iterator[Token | Answer | ActionToApprove]:
        """Les morceaux de la réponse, puis la réponse complète ou l'action à valider, en dernier."""
        ...

    def resume(self, conversation_id: str, user: User, approved: bool) -> Answer | ActionToApprove:
        """Reprend la conversation en pause : l'action proposée est exécutée ou refusée."""
        ...
