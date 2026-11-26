"""Lancer l'API web : uv run --env-file .env assistant api"""

from collections.abc import Mapping

import uvicorn

from assistant.application.assistant import Assistant
from assistant.entrypoints.web_api.app import create_app

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def run(assistant: Assistant, settings: Mapping[str, str]) -> None:
    # La clé est obligatoire : une API sans clé laisserait n'importe qui consommer le modèle
    app = create_app(assistant, api_key=settings["API_KEY"])
    uvicorn.run(
        app, host=settings.get("API_HOST", DEFAULT_HOST), port=int(settings.get("API_PORT", DEFAULT_PORT))
    )
