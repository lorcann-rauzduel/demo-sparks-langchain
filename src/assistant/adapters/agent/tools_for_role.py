"""Les droits : un middleware retire au modèle les outils que le rôle de l'utilisateur n'autorise pas."""

from collections.abc import Callable
from typing import Any

from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call

from assistant.adapters.agent.agent_context import AgentContext
from assistant.adapters.agent.tools.tickets import CLOSE_TICKET

SUPPORT_ONLY_TOOLS = frozenset({CLOSE_TICKET})


@wrap_model_call
def tools_for_role(
    request: ModelRequest[AgentContext], handler: Callable[[ModelRequest[AgentContext]], ModelResponse[Any]]
) -> ModelResponse[Any]:
    # Un outil absent de la requête ne peut pas être appelé : la règle ne dépend pas du prompt
    if request.runtime.context.role != "support":
        allowed = [tool for tool in request.tools if getattr(tool, "name", None) not in SUPPORT_ONLY_TOOLS]
        request = request.override(tools=allowed)
    return handler(request)
