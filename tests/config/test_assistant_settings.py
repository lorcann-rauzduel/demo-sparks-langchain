from assistant.config.assistant_settings import DEFAULT_MAX_QUESTION_LENGTH, AssistantSettings


def test_without_environment_the_documented_default_applies() -> None:
    assert AssistantSettings.from_environment({}).max_question_length == DEFAULT_MAX_QUESTION_LENGTH


def test_a_value_from_the_environment_replaces_the_default() -> None:
    assert AssistantSettings.from_environment({"MAX_QUESTION_LENGTH": "100"}).max_question_length == 100


def test_the_support_team_is_a_comma_separated_list_of_user_ids() -> None:
    settings = AssistantSettings.from_environment({"SUPPORT_USERS": "terminal, discord:99,"})

    assert settings.support_users == frozenset({"terminal", "discord:99"})
