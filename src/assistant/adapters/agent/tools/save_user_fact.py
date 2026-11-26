"""La mémoire long terme : l'outil qui range un fait durable sur l'utilisateur dans le store."""

from langchain.tools import ToolRuntime, tool
from langchain_core.tools import BaseTool

from assistant.adapters.agent.agent_context import AgentContext

PROFILE_KEY = "profile"


def user_namespace(user_id: str) -> tuple[str, str]:
    # Un espace de noms par utilisateur : les faits de l'un ne sont jamais lus pour un autre
    return ("users", user_id)


def save_user_fact_tool() -> BaseTool:
    @tool(parse_docstring=True)
    def save_user_fact(fact: str, runtime: ToolRuntime[AgentContext]) -> str:
        """Save one lasting fact about the user, such as their office, team or preferences. Never small talk.

        Args:
            fact: The fact, in one short sentence.
        """
        assert runtime.store is not None
        # L'identifiant vient du contexte d'exécution, donc du code : le modèle ne peut pas le choisir
        namespace = user_namespace(runtime.context.user_id)
        profile = runtime.store.get(namespace, PROFILE_KEY)
        facts = profile.value["facts"] if profile else []
        runtime.store.put(namespace, PROFILE_KEY, {"facts": [*facts, fact]})
        return "Saved."

    return save_user_fact
