"""L'index des documents : la base vectorielle du RAG (Chroma), séparée de la base de la mémoire."""

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from assistant.config.index_settings import IndexSettings

DOCUMENT_PATTERN = "*.md"


def build_index(settings: IndexSettings) -> Chroma:
    """Charge les documents, les découpe, vectorise les morceaux et les enregistre."""
    documents = DirectoryLoader(str(settings.corpus_dir), glob=DOCUMENT_PATTERN, loader_cls=TextLoader).load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )
    chunks = splitter.split_documents(documents)

    return Chroma.from_documents(chunks, _embeddings(settings), persist_directory=str(settings.index_dir))


def open_index(settings: IndexSettings) -> Chroma:
    return Chroma(persist_directory=str(settings.index_dir), embedding_function=_embeddings(settings))


def _embeddings(settings: IndexSettings) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)
