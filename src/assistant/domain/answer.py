"""Les objets du cœur : ce que l'assistant renvoie, indépendamment de tout framework."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Answer:
    text: str
    sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class Token:
    """Un morceau de réponse en cours d'écriture, pour les canaux qui affichent un flux."""

    text: str


@dataclass(frozen=True)
class ActionToApprove:
    """Les actions que l'agent veut exécuter : elles attendent la décision de l'utilisateur."""

    actions: tuple[str, ...]
