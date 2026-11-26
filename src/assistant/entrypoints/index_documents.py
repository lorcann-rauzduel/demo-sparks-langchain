"""Indexer les documents de l'entreprise, une fois, avant de lancer un canal.

uv run --env-file .env assistant-index
"""

import os

from assistant.adapters.documents.chroma_index import build_index
from assistant.config.index_settings import IndexSettings


def main() -> None:
    settings = IndexSettings.from_environment(os.environ)
    build_index(settings)
    print(f"Index construit dans {settings.index_dir}/ à partir de {settings.corpus_dir}/.")


if __name__ == "__main__":
    main()
