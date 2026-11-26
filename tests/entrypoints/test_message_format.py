from assistant.domain.answer import Answer
from assistant.entrypoints.message_format import format_answer, format_sources


def test_sources_follow_the_answer() -> None:
    assert format_answer(Answer("Ten days.", sources=("leave_2026.md", "faq.md"))) == (
        "Ten days.\n\nSources : leave_2026.md, faq.md"
    )


def test_an_answer_without_sources_is_shown_as_is() -> None:
    assert format_answer(Answer("Hello!")) == "Hello!"


def test_after_a_stream_only_the_sources_remain_to_show() -> None:
    assert format_sources(Answer("Ten days.", sources=("leave.md",))) == "\n\nSources : leave.md"
    assert format_sources(Answer("Hello!")) == ""
