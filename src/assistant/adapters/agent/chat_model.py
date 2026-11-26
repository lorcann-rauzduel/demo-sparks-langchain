"""Le modèle de langage, choisi par son nom « fournisseur:modèle »."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

OLLAMA_PREFIX = "ollama:"


def load_chat_model(model: str) -> BaseChatModel:
    # Avec Ollama, reasoning=False coupe la phase de réflexion du petit modèle local
    if model.startswith(OLLAMA_PREFIX):
        return init_chat_model(model, reasoning=False)
    return init_chat_model(model)
