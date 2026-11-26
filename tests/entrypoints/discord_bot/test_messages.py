from assistant.entrypoints.discord_bot.messages import question_from_message, split_message


def test_in_a_server_the_bot_answers_only_when_mentioned_and_without_the_mention() -> None:
    assert question_from_message("<@99> Leave notice?", bot_id=99, is_private=False) == "Leave notice?"
    assert question_from_message("Hello everyone", bot_id=99, is_private=False) is None
    assert question_from_message("Hello", bot_id=99, is_private=True) == "Hello"


def test_a_short_message_is_sent_in_one_piece() -> None:
    assert split_message("Hello!", max_length=10) == ["Hello!"]


def test_a_long_message_is_cut_at_line_breaks_within_the_limit() -> None:
    text = "first line\nsecond line\nthird"

    assert split_message(text, max_length=12) == ["first line", "second line", "third"]


def test_a_line_longer_than_the_limit_is_cut_at_the_limit() -> None:
    assert split_message("abcdefghij", max_length=4) == ["abcd", "efgh", "ij"]
