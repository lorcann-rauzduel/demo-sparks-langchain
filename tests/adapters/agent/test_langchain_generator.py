from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from assistant.adapters.agent.company_agent import build_company_agent
from assistant.adapters.agent.langchain_generator import LangChainGenerator
from assistant.adapters.documents.chroma_index import build_index
from assistant.adapters.tickets.sqlite_tickets import SqliteTickets
from assistant.config.agent_settings import AgentSettings
from assistant.config.index_settings import IndexSettings
from assistant.domain.answer import ActionToApprove, Answer, Token
from assistant.domain.user import User

pytestmark = pytest.mark.groq  # ces tests appellent le vrai modèle : uv run --env-file .env pytest -m groq

DEFAULT_AGENT_SETTINGS = AgentSettings.from_environment({})
TERMINAL = User("terminal", "employee")

GeneratorFactory = Callable[..., LangChainGenerator]


def TICKETS_DB(tmp_path: Path) -> Path:
    return tmp_path / "tickets.db"


@pytest.fixture
def make_generator(tmp_path: Path) -> GeneratorFactory:
    documents = build_index(replace(IndexSettings.from_environment({}), index_dir=tmp_path / "index"))
    tickets = SqliteTickets.open(TICKETS_DB(tmp_path), Path("data/tickets.sql"))

    def generator_for(
        settings: AgentSettings = DEFAULT_AGENT_SETTINGS, checkpointer: InMemorySaver | None = None
    ) -> LangChainGenerator:
        agent = build_company_agent(
            settings, documents, tickets, checkpointer or InMemorySaver(), InMemoryStore()
        )
        return LangChainGenerator(agent)

    return generator_for


def answer_to(generator: LangChainGenerator, conversation_id: str, user: User, question: str) -> Answer:
    """A question that needs no approval: the result is always a complete answer."""
    result = generator.generate(conversation_id, user, question)
    assert isinstance(result, Answer)
    return result


def test_the_model_answers(make_generator: GeneratorFactory) -> None:
    answer = answer_to(make_generator(), "terminal#0", TERMINAL, "Say hello in one word.")

    assert answer.text.strip()


def test_a_conversation_remembers_its_own_messages_only(make_generator: GeneratorFactory) -> None:
    # Un détail de la conversation, pas un fait durable : il ne passe pas dans la mémoire long terme
    generator = make_generator()
    generator.generate("terminal#0", TERMINAL, "For this conversation only, the code word is 'heron'.")

    same = answer_to(generator, "terminal#0", TERMINAL, "What is the code word? One word.")
    other = answer_to(
        generator,
        "terminal#1",
        TERMINAL,
        "What is the code word? One word, or 'unknown'.",
    )

    assert "heron" in same.text.lower()
    assert "heron" not in other.text.lower()


def test_a_lasting_fact_is_remembered_in_a_new_conversation_of_the_same_user_only(
    make_generator: GeneratorFactory,
) -> None:
    generator = make_generator()
    generator.generate(
        "discord:1#0", User("discord:1", "employee"), "Remember this: I work at the Lyon office."
    )

    same_user = answer_to(
        generator, "discord:1#1", User("discord:1", "employee"), "Which city is my office in? One word."
    )
    other_user = answer_to(
        generator,
        "discord:2#0",
        User("discord:2", "employee"),
        "Which city is my office in? One word, or 'unknown'.",
    )

    assert "lyon" in same_user.text.lower()
    assert "lyon" not in other_user.text.lower()


def test_an_answer_from_the_documents_comes_with_its_sources(make_generator: GeneratorFactory) -> None:
    answer = answer_to(make_generator(), "terminal#0", TERMINAL, "What should I do with error ERR-4012?")

    assert "securite.md" in answer.sources


def test_a_question_about_a_ticket_is_answered_from_the_business_database(
    make_generator: GeneratorFactory,
) -> None:
    answer = answer_to(make_generator(), "terminal#0", TERMINAL, "What is the status of ticket 4?")

    assert "open" in answer.text.lower()


def test_the_answer_streams_in_several_pieces_then_ends_with_its_sources(
    make_generator: GeneratorFactory,
) -> None:
    *pieces, final = make_generator().stream("terminal#0", TERMINAL, "What should I do with error ERR-4012?")

    assert len(pieces) > 1 and all(isinstance(piece, Token) for piece in pieces)
    assert isinstance(final, Answer) and "securite.md" in final.sources


def test_a_long_conversation_is_compacted_into_a_summary(make_generator: GeneratorFactory) -> None:
    checkpointer = InMemorySaver()
    generator = make_generator(replace(DEFAULT_AGENT_SETTINGS, summary_trigger_tokens=300), checkpointer)

    for question in ["I am Camille.", "I like short answers.", "What is LangChain?", "What is RAG?"]:
        generator.generate("terminal#0", TERMINAL, question)

    saved = checkpointer.get_tuple({"configurable": {"thread_id": "terminal#0"}})
    assert saved is not None
    assert len(saved.checkpoint["channel_values"]["messages"]) < 8


LEAVE_REQUEST = "Submit a leave request from 2026-12-21 to 2026-12-24."


def test_a_leave_request_waits_for_approval_then_is_submitted(make_generator: GeneratorFactory) -> None:
    generator = make_generator()

    action = generator.generate("terminal#0", TERMINAL, LEAVE_REQUEST)
    assert isinstance(action, ActionToApprove)
    assert "submit_leave_request" in action.actions[0] and "2026-12-21" in action.actions[0]

    answer = generator.resume("terminal#0", TERMINAL, approved=True)
    assert isinstance(answer, Answer) and "LEAVE-" in answer.text


def test_a_refused_leave_request_is_not_submitted(make_generator: GeneratorFactory) -> None:
    generator = make_generator()
    generator.generate("terminal#0", TERMINAL, LEAVE_REQUEST)

    answer = generator.resume("terminal#0", TERMINAL, approved=False)

    assert isinstance(answer, Answer) and "LEAVE-" not in answer.text


def test_a_streamed_leave_request_ends_on_the_action_to_approve(make_generator: GeneratorFactory) -> None:
    *_, final = make_generator().stream("terminal#0", TERMINAL, LEAVE_REQUEST)

    assert isinstance(final, ActionToApprove)


def test_a_question_during_a_pause_gets_the_same_action_back(make_generator: GeneratorFactory) -> None:
    generator = make_generator()
    action = generator.generate("terminal#0", TERMINAL, LEAVE_REQUEST)

    assert generator.generate("terminal#0", TERMINAL, "What is RAG?") == action


SUPPORT = User("discord:99", "support")
EMPLOYEE = User("discord:1", "employee")
CLOSE_REQUEST = "Close ticket 2."


def test_an_employee_cannot_close_a_ticket(make_generator: GeneratorFactory, tmp_path: Path) -> None:
    result = make_generator().generate("discord:1#0", EMPLOYEE, CLOSE_REQUEST)

    assert isinstance(result, Answer)
    assert (
        SqliteTickets(TICKETS_DB(tmp_path)).status(2)
        == "Ticket 2: Printer offline on floor 2, open, priority low."
    )


def test_the_support_closes_a_ticket_after_approval(make_generator: GeneratorFactory, tmp_path: Path) -> None:
    generator = make_generator()

    action = generator.generate("discord:99#0", SUPPORT, CLOSE_REQUEST)
    assert isinstance(action, ActionToApprove) and "close_ticket" in action.actions[0]

    generator.resume("discord:99#0", SUPPORT, approved=True)
    assert "closed" in (SqliteTickets(TICKETS_DB(tmp_path)).status(2) or "")
