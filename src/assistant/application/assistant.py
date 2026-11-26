"""Le cas d'usage : répondre à un utilisateur, quel que soit le canal qui l'appelle."""

from collections.abc import Iterator

from assistant.application.ports.answer_generator import AnswerGenerator
from assistant.application.ports.conversation_registry import ConversationRegistry
from assistant.application.ports.user_roles import UserRoles
from assistant.domain.answer import ActionToApprove, Answer, Token
from assistant.domain.user import User

NEW_CONVERSATION_COMMAND = "/new"
REFUSAL = "I don't know."


class Assistant:
    def __init__(
        self,
        generator: AnswerGenerator,
        conversations: ConversationRegistry,
        roles: UserRoles,
        max_question_length: int,
    ) -> None:
        self._generator = generator
        self._conversations = conversations
        self._roles = roles
        self._max_question_length = max_question_length

    def answer(self, user_id: str, question: str) -> Answer | ActionToApprove:
        """La réponse complète, pour les canaux qui l'affichent d'un bloc."""
        reply = self._reply_without_model(user_id, question)
        if reply is not None:
            return reply

        conversation_id = self._conversations.current(user_id)
        answer = self._generator.generate(conversation_id, self._user(user_id), question)
        return _without_sources_if_refused(answer)

    def stream(self, user_id: str, question: str) -> Iterator[Token | Answer | ActionToApprove]:
        """Les morceaux de la réponse, puis la réponse complète, soumise aux mêmes règles."""
        reply = self._reply_without_model(user_id, question)
        if reply is not None:
            yield reply
            return

        conversation_id = self._conversations.current(user_id)
        for piece in self._generator.stream(conversation_id, self._user(user_id), question):
            yield piece if isinstance(piece, Token) else _without_sources_if_refused(piece)

    def decide(self, user_id: str, approved: bool) -> Answer | ActionToApprove:
        """Reprend la conversation en pause avec la décision de l'utilisateur sur l'action proposée."""
        conversation_id = self._conversations.current(user_id)
        return _without_sources_if_refused(
            self._generator.resume(conversation_id, self._user(user_id), approved)
        )

    def _user(self, user_id: str) -> User:
        # Le rôle est décidé par le cœur, jamais par le modèle ni par le texte de la question
        return User(user_id, self._roles.role_of(user_id))

    def _reply_without_model(self, user_id: str, question: str) -> Answer | None:
        """La réponse quand le modèle n'a pas besoin d'être appelé, sinon None."""
        question = question.strip()

        if question == NEW_CONVERSATION_COMMAND:
            self._conversations.start_new(user_id)
            return Answer("New conversation started.")

        if not question:
            return Answer("Please ask a question.")

        # Une question trop longue coûte cher : elle n'est jamais envoyée au modèle
        if len(question) > self._max_question_length:
            return Answer(f"Your question is too long ({self._max_question_length} characters maximum).")

        return None


def _without_sources_if_refused(answer: Answer | ActionToApprove) -> Answer | ActionToApprove:
    if isinstance(answer, ActionToApprove):
        return answer
    # Afficher les passages consultés avec un refus ferait croire à une réponse
    return Answer(REFUSAL) if answer.text.strip() == REFUSAL else answer
