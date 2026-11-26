import pytest

from assistant.domain.answer import ActionToApprove
from assistant.entrypoints import terminal
from tests.entrypoints.stubs import assistant_answering


def chat(monkeypatch: pytest.MonkeyPatch, *questions: str) -> None:
    lines = iter([*questions, ""])  # une ligne vide quitte le terminal
    monkeypatch.setattr("builtins.input", lambda prompt: next(lines))


def test_the_answer_is_streamed_by_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assistant, _ = assistant_answering("Ten days.")
    chat(monkeypatch, "Leave notice?")

    terminal.run(assistant, settings={})

    # Le stub envoie « Ten » puis « days. » : en flux, les morceaux s'affichent bout à bout
    assert "Tendays.\n" in capsys.readouterr().out


def test_without_streaming_the_answer_is_printed_in_one_block(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assistant, _ = assistant_answering("Ten days.")
    chat(monkeypatch, "Leave notice?")

    terminal.run(assistant, settings={"TERMINAL_STREAMING": "off"})

    assert "Ten days.\n" in capsys.readouterr().out


LEAVE_REQUEST = ActionToApprove(("submit_leave_request(start_date='2026-12-21', end_date='2026-12-24')",))


@pytest.mark.parametrize("settings", [{}, {"TERMINAL_STREAMING": "off"}])
def test_an_action_is_shown_and_runs_only_once_the_user_approves_it(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], settings: dict[str, str]
) -> None:
    assistant, generator = assistant_answering("Leave request submitted.", LEAVE_REQUEST)
    chat(monkeypatch, "Book my leave", "o")

    terminal.run(assistant, settings)

    out = capsys.readouterr().out
    assert "submit_leave_request(start_date='2026-12-21', end_date='2026-12-24')" in out
    assert "Leave request submitted.\n" in out
    assert generator.decisions == [True]


def test_any_other_reply_refuses_the_action(monkeypatch: pytest.MonkeyPatch) -> None:
    assistant, generator = assistant_answering("The leave request was not submitted.", LEAVE_REQUEST)
    chat(monkeypatch, "Book my leave", "n")

    terminal.run(assistant, settings={})

    assert generator.decisions == [False]
