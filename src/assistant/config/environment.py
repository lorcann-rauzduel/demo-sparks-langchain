"""La lecture d'un réglage dans l'environnement (.env), avec sa valeur par défaut."""

from collections.abc import Mapping


def read_setting(environment: Mapping[str, str], name: str, default: str | int) -> str:
    return environment.get(name, str(default))
