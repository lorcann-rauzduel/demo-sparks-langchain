"""Les réglages de l'index des documents : où les lire, comment les découper, où ranger leurs vecteurs."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from assistant.config.environment import read_setting

DEFAULT_CORPUS_DIR = "corpus"
DEFAULT_INDEX_DIR = "chroma_db"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50


@dataclass(frozen=True)
class IndexSettings:
    corpus_dir: Path
    index_dir: Path
    embedding_model: str  # le même modèle à l'indexation et à la recherche
    chunk_size: int  # en caractères
    chunk_overlap: int  # en caractères

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> "IndexSettings":
        def read(name: str, default: str | int) -> str:
            return read_setting(environment, name, default)

        return cls(
            corpus_dir=Path(read("CORPUS_DIR", DEFAULT_CORPUS_DIR)),
            index_dir=Path(read("INDEX_DIR", DEFAULT_INDEX_DIR)),
            embedding_model=read("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL),
            chunk_size=int(read("CHUNK_SIZE", DEFAULT_CHUNK_SIZE)),
            chunk_overlap=int(read("CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP)),
        )
