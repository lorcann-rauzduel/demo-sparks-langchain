from collections.abc import Iterator

from assistant.adapters.conversations.in_memory import InMemoryConversations
from assistant.adapters.users.configured_roles import ConfiguredRoles
from assistant.application.assistant import Assistant
from assistant.domain.answer import ActionToApprove, Answer, Token
from assistant.domain.user import User

MAX_QUESTION_LENGTH = 2000


class StubGenerator:
    """Answers with a fixed text, in one piece or token by token, and records the conversations.

    With an action, it first asks for its approval, then answers with the text once the user has decided.
    """

    def __init__(self, text: str, action: ActionToApprove | None = None) -> None:
        self.text = text
        self.action = action
        self.conversations: list[str] = []
        self.decisions: list[bool] = []

    def generate(self, conversation_id: str, user: User, question: str) -> Answer | ActionToApprove:
        self.conversations.append(conversation_id)
        return self.action or Answer(self.text)

    def stream(
        self, conversation_id: str, user: User, question: str
    ) -> Iterator[Token | Answer | ActionToApprove]:
        self.conversations.append(conversation_id)
        if self.action:
            yield self.action
            return
        yield from (Token(word) for word in self.text.split(" "))
        yield Answer(self.text)

    def resume(self, conversation_id: str, user: User, approved: bool) -> Answer | ActionToApprove:
        self.decisions.append(approved)
        return Answer(self.text)


def assistant_answering(text: str, action: ActionToApprove | None = None) -> tuple[Assistant, StubGenerator]:
    generator = StubGenerator(text, action)
    return Assistant(
        generator, InMemoryConversations(), ConfiguredRoles(frozenset()), MAX_QUESTION_LENGTH
    ), generator
