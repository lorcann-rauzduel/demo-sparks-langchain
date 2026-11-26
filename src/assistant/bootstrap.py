"""Racine de composition : le seul endroit qui assemble le cœur et ses adaptateurs."""

from collections.abc import Mapping

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from assistant.adapters.agent.company_agent import build_company_agent
from assistant.adapters.agent.langchain_generator import LangChainGenerator
from assistant.adapters.conversations.in_memory import InMemoryConversations
from assistant.adapters.documents.chroma_index import open_index
from assistant.adapters.tickets.sqlite_tickets import SqliteTickets
from assistant.adapters.users.configured_roles import ConfiguredRoles
from assistant.application.assistant import Assistant
from assistant.config.agent_settings import AgentSettings
from assistant.config.assistant_settings import AssistantSettings
from assistant.config.index_settings import IndexSettings
from assistant.config.tickets_settings import TicketsSettings


def build_assistant(environment: Mapping[str, str]) -> Assistant:
    # En production : PostgresSaver, pour que les conversations survivent au redémarrage
    checkpointer = InMemorySaver()
    # En production : PostgresStore, pour que les faits durables survivent au redémarrage
    store = InMemoryStore()

    agent_settings = AgentSettings.from_environment(environment)
    documents = open_index(IndexSettings.from_environment(environment))
    tickets_settings = TicketsSettings.from_environment(environment)
    tickets = SqliteTickets.open(tickets_settings.database, tickets_settings.seed)
    agent = build_company_agent(agent_settings, documents, tickets, checkpointer, store)

    rules = AssistantSettings.from_environment(environment)
    return Assistant(
        LangChainGenerator(agent),
        InMemoryConversations(),
        ConfiguredRoles(rules.support_users),
        rules.max_question_length,
    )
