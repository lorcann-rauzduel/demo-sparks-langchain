"""L'agent de l'entreprise : le modèle et ses briques, assemblés avec create_agent."""

from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    ModelRequest,
    SummarizationMiddleware,
    dynamic_prompt,
)
from langchain_core.vectorstores import VectorStore
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.store.base import BaseStore

from assistant.adapters.agent.agent_context import AgentContext
from assistant.adapters.agent.chat_model import load_chat_model
from assistant.adapters.agent.tools.save_user_fact import PROFILE_KEY, save_user_fact_tool, user_namespace
from assistant.adapters.agent.tools.search_company_documents import search_company_documents_tool
from assistant.adapters.agent.tools.submit_leave_request import TOOL_NAME, submit_leave_request_tool
from assistant.adapters.agent.tools.tickets import CLOSE_TICKET, close_ticket_tool, get_ticket_status_tool
from assistant.adapters.agent.tools_for_role import tools_for_role
from assistant.adapters.tickets.sqlite_tickets import SqliteTickets
from assistant.config.agent_settings import AgentSettings


def build_company_agent(
    settings: AgentSettings,
    documents: VectorStore,
    tickets: SqliteTickets,
    checkpointer: BaseCheckpointSaver[str],
    store: BaseStore,
) -> CompiledStateGraph[Any, Any, Any, Any]:
    model = load_chat_model(settings.model)
    system_prompt = settings.system_prompt_file.read_text(encoding="utf-8").strip()

    # Mémoire long terme, en lecture : les faits connus sur l'utilisateur rejoignent le prompt à chaque appel
    @dynamic_prompt
    def prompt_with_user_facts(request: ModelRequest[AgentContext]) -> str:
        assert request.runtime.store is not None
        profile = request.runtime.store.get(user_namespace(request.runtime.context.user_id), PROFILE_KEY)
        if profile is None:
            return system_prompt
        return f"{system_prompt}\n\nKnown facts about the user: {'; '.join(profile.value['facts'])}"

    return create_agent(
        model=model,
        tools=[
            search_company_documents_tool(documents, settings.passages_per_search),
            get_ticket_status_tool(tickets),
            close_ticket_tool(tickets),
            submit_leave_request_tool(),
            save_user_fact_tool(),
        ],
        middleware=[
            prompt_with_user_facts,
            # Droits : avant chaque appel au modèle, les outils du support sont retirés aux autres
            tools_for_role,
            # Validation humaine : l'agent s'arrête avant chaque action, jusqu'à la décision de l'utilisateur
            HumanInTheLoopMiddleware(
                interrupt_on={
                    name: {"allowed_decisions": ["approve", "reject"]} for name in (TOOL_NAME, CLOSE_TICKET)
                },
            ),
            # Au-delà du seuil, les anciens messages sont remplacés par un résumé
            SummarizationMiddleware(
                model=model,
                trigger=("tokens", settings.summary_trigger_tokens),
                keep=("messages", settings.messages_kept_after_summary),
            ),
            # Coût : au plus N appels au modèle par question, puis l'agent s'arrête avec la réponse en cours
            ModelCallLimitMiddleware(run_limit=settings.model_call_limit, exit_behavior="end"),  # type: ignore[list-item]
        ],
        # Mémoire court terme : chaque fil de conversation est enregistré à chaque étape
        checkpointer=checkpointer,
        # Mémoire long terme : les faits durables, rangés par utilisateur, partagés entre ses conversations
        store=store,
        context_schema=AgentContext,
    )
