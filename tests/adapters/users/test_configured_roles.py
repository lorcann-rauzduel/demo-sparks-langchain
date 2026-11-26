from assistant.adapters.users.configured_roles import ConfiguredRoles


def test_only_the_listed_users_have_the_support_role() -> None:
    roles = ConfiguredRoles(frozenset({"discord:99"}))

    assert roles.role_of("discord:99") == "support"
    assert roles.role_of("discord:1") == "employee"
