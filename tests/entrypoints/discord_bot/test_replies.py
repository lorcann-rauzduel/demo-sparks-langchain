from assistant.domain.answer import ActionToApprove
from assistant.entrypoints.discord_bot.messages import discord_user, replies_for
from tests.entrypoints.stubs import assistant_answering


def test_a_discord_user_gets_their_own_conversation_and_replies_within_2000_characters() -> None:
    assistant, generator = assistant_answering("x" * 2500)

    replies = replies_for(assistant.answer(discord_user(7), "Hello"))

    assert generator.conversations == ["discord:7#0"]
    assert [len(reply) for reply in replies] == [2000, 500]


def test_an_action_to_approve_is_described_before_the_buttons() -> None:
    action = ActionToApprove(("submit_leave_request(start_date='2026-12-21', end_date='2026-12-24')",))

    (reply,) = replies_for(action)

    assert "submit_leave_request(start_date='2026-12-21', end_date='2026-12-24')" in reply
