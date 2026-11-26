"""L'outil de recherche dans les documents de l'entreprise, que le modèle appelle quand il en a besoin."""

from langchain.tools import tool
from langchain_core.documents import Document
from langchain_core.tools import BaseTool
from langchain_core.vectorstores import VectorStore


def search_company_documents_tool(documents: VectorStore, passages_per_search: int) -> BaseTool:
    @tool(response_format="content_and_artifact", parse_docstring=True)
    def search_company_documents(query: str) -> tuple[str, list[Document]]:
        """Search the company documents: leave, remote work, expenses, security and error codes.

        Args:
            query: What to look for, in the words of the user's question.
        """
        passages = documents.similarity_search(query, k=passages_per_search)

        # Le texte part au modèle ; les Documents restent attachés au message de l'outil, pour les sources
        text_for_the_model = "\n\n".join(passage.page_content for passage in passages)
        return text_for_the_model, passages

    return search_company_documents
