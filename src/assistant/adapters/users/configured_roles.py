"""Adaptateur du port UserRoles : l'équipe support est une liste d'identifiants, lue dans les réglages.

En production, le rôle viendrait de l'annuaire de l'entreprise (LDAP, SSO, base des comptes).
"""

from assistant.domain.user import Role


class ConfiguredRoles:
    def __init__(self, support_users: frozenset[str]) -> None:
        self._support_users = support_users

    def role_of(self, user_id: str) -> Role:
        return "support" if user_id in self._support_users else "employee"
