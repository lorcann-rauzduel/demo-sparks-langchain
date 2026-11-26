from assistant.adapters.conversations.in_memory import InMemoryConversations


def test_a_new_conversation_gets_a_new_identifier_for_that_user_only() -> None:
    conversations = InMemoryConversations()
    first = conversations.current("discord:42")

    conversations.start_new("discord:42")

    assert conversations.current("discord:42") != first
    assert conversations.current("discord:7") == conversations.current("discord:7")
