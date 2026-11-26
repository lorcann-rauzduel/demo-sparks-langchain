from collections.abc import Iterator

from assistant.adapters.conversations.in_memory import InMemoryConversations
from assistant.adapters.users.configured_roles import ConfiguredRoles
from assistant.application.assistant import Assistant
from assistant.domain.answer import ActionToApprove, Answer, Token
from assistant.domain.user import User

MAX_QUESTION_LENGTH = 20


class StubGenerator:
    """Returns fixed pieces and records what it was asked."""

    def __init__(self, *pieces: Token | Answer | ActionToApprove) -> None:
        self.pieces = pieces
        self.calls: list[tuple[str, User, str]] = []
        self.decisions: list[tuple[str, User, bool]] = []

    def generate(self, conversation_id: str, user: User, question: str) -> Answer | ActionToApprove:
        self.calls.append((conversation_id, user, question))
        result = self.pieces[-1]
        assert not isinstance(result, Token)
        return result

    def stream(
        self, conversation_id: str, user: User, question: str
    ) -> Iterator[Token | Answer | ActionToApprove]:
        self.calls.append((conversation_id, user, question))
        yield from self.pieces

    def resume(self, conversation_id: str, user: User, approved: bool) -> Answer | ActionToApprove:
        self.decisions.append((conversation_id, user, approved))
        result = self.pieces[-1]
        assert not isinstance(result, Token)
        return result


SUPPORT_USER = "discord:99"


def assistant_with(generator: StubGenerator) -> Assistant:
    roles = ConfiguredRoles(support_users=frozenset({SUPPORT_USER}))
    return Assistant(generator, InMemoryConversations(), roles, MAX_QUESTION_LENGTH)


def test_answers_in_the_current_conversation_of_the_user() -> None:
    generator = StubGenerator(Answer("Ten days.", sources=("leave_2026.md",)))

    answer = assistant_with(generator).answer("discord:42", "Leave notice?")

    assert answer == Answer("Ten days.", sources=("leave_2026.md",))
    assert generator.calls == [("discord:42#0", User("discord:42", "employee"), "Leave notice?")]


def test_an_empty_question_is_refused_without_calling_the_model() -> None:
    generator = StubGenerator(Answer("unused"))

    assert assistant_with(generator).answer("terminal", "   ") == Answer("Please ask a question.")
    assert generator.calls == []


def test_a_question_too_long_is_refused_without_calling_the_model() -> None:
    generator = StubGenerator(Answer("unused"))

    answer = assistant_with(generator).answer("terminal", "x" * (MAX_QUESTION_LENGTH + 1))

    assert answer == Answer("Your question is too long (20 characters maximum).")
    assert generator.calls == []


def test_new_starts_a_new_conversation_without_calling_the_model() -> None:
    generator = StubGenerator(Answer("unused"))
    assistant = assistant_with(generator)

    assert assistant.answer("discord:7", "/new") == Answer("New conversation started.")
    assistant.answer("discord:7", "Hello")

    assert generator.calls == [("discord:7#1", User("discord:7", "employee"), "Hello")]


def test_a_refusal_shows_no_sources() -> None:
    generator = StubGenerator(Answer("I don't know.", sources=("remote_work.md",)))

    assert assistant_with(generator).answer("terminal", "Salary?") == Answer("I don't know.")


def test_streams_the_pieces_then_the_complete_answer() -> None:
    pieces = (Token("Ten "), Token("days."), Answer("Ten days.", sources=("leave.md",)))
    generator = StubGenerator(*pieces)

    assert list(assistant_with(generator).stream("terminal", "Leave notice?")) == list(pieces)
    assert generator.calls == [("terminal#0", User("terminal", "employee"), "Leave notice?")]


def test_a_streamed_answer_follows_the_same_rules() -> None:
    generator = StubGenerator(Token("I don't know."), Answer("I don't know.", ("remote_work.md",)))
    assistant = assistant_with(generator)

    assert list(assistant.stream("terminal", "  ")) == [Answer("Please ask a question.")]
    assert list(assistant.stream("terminal", "Salary?"))[-1] == Answer("I don't know.")


def test_an_action_to_approve_is_passed_to_the_channel() -> None:
    action = ActionToApprove(("submit_leave_request(start_date='2026-12-21', end_date='2026-12-24')",))
    generator = StubGenerator(action)

    assert assistant_with(generator).answer("terminal", "Book my leave") == action


def test_the_decision_resumes_the_current_conversation_of_the_user() -> None:
    generator = StubGenerator(Answer("Your leave request is submitted."))

    answer = assistant_with(generator).decide("discord:42", approved=True)

    assert answer == Answer("Your leave request is submitted.")
    assert generator.decisions == [("discord:42#0", User("discord:42", "employee"), True)]


def test_a_user_listed_in_the_support_team_has_the_support_role() -> None:
    generator = StubGenerator(Answer("Closed."))

    assistant_with(generator).answer(SUPPORT_USER, "Close ticket 2")

    assert generator.calls == [("discord:99#0", User(SUPPORT_USER, "support"), "Close ticket 2")]
