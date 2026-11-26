"""Adaptateur du port AnswerGenerator avec un agent LangChain. Douane : aucun type LangChain n'en sort."""

from collections.abc import Iterator
from pathlib import PurePath
from typing import Any

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from assistant.adapters.agent.agent_context import AgentContext
from assistant.domain.answer import ActionToApprove, Answer, Token
from assistant.domain.user import User

MODEL_STEP = "model"  # l'étape de l'agent qui écrit la réponse
REFUSED_BY_USER = "The user refused this action. Do not retry it; say that it was not done."


class LangChainGenerator:
    def __init__(self, agent: CompiledStateGraph[Any, Any, Any, Any]) -> None:
        self._agent = agent

    def generate(self, conversation_id: str, user: User, question: str) -> Answer | ActionToApprove:
        thread = _thread(conversation_id)
        # Une conversation en pause attend d'abord la décision sur l'action proposée
        if pending := self._action_to_approve(thread):
            return pending

        self._agent.invoke(_user_message(question), thread, context=AgentContext.of(user))
        return self._result(thread)

    def resume(self, conversation_id: str, user: User, approved: bool) -> Answer | ActionToApprove:
        thread = _thread(conversation_id)
        pending = self._action_to_approve(thread)
        if pending is None:
            return self._result(thread)

        # Une décision par action proposée, dans le même ordre
        decision = {"type": "approve"} if approved else {"type": "reject", "message": REFUSED_BY_USER}
        decisions = {"decisions": [decision] * len(pending.actions)}
        self._agent.invoke(Command(resume=decisions), thread, context=AgentContext.of(user))
        return self._result(thread)

    def stream(
        self, conversation_id: str, user: User, question: str
    ) -> Iterator[Token | Answer | ActionToApprove]:
        thread = _thread(conversation_id)
        if pending := self._action_to_approve(thread):
            yield pending
            return

        # stream_mode="messages" : un morceau par token, au fur et à mesure qu'il est produit
        for chunk in self._agent.stream(
            _user_message(question),
            thread,
            context=AgentContext.of(user),
            stream_mode="messages",
            version="v2",
        ):
            if chunk["type"] != "messages":
                continue
            token, metadata = chunk["data"]
            # Seuls les morceaux de l'étape « model » forment la réponse ; ceux de l'outil sont ignorés
            if metadata["langgraph_node"] == MODEL_STEP and token.text:
                yield Token(token.text)

        # La réponse complète, avec ses sources, est relue dans le fil enregistré par le checkpointer
        yield self._result(thread)

    def _result(self, thread: RunnableConfig) -> Answer | ActionToApprove:
        """L'action qui attend une décision si l'agent est en pause, sinon la réponse complète."""
        return self._action_to_approve(thread) or _to_answer(self._agent.get_state(thread).values["messages"])

    def _action_to_approve(self, thread: RunnableConfig) -> ActionToApprove | None:
        # HumanInTheLoopMiddleware met l'agent en pause : la pause est enregistrée dans le fil
        interrupts = self._agent.get_state(thread).interrupts
        if not interrupts:
            return None
        requests = [request for interrupt in interrupts for request in interrupt.value["action_requests"]]
        return ActionToApprove(tuple(_describe(request["name"], request["args"]) for request in requests))


def _describe(name: str, args: dict[str, Any]) -> str:
    arguments = ", ".join(f"{key}={value!r}" for key, value in args.items())
    return f"{name}({arguments})"


def _user_message(question: str) -> dict[str, list[dict[str, str]]]:
    return {"messages": [{"role": "user", "content": question}]}


def _thread(conversation_id: str) -> RunnableConfig:
    # Une conversation du cœur = un fil (thread) du checkpointer
    return {"configurable": {"thread_id": conversation_id}}


def _to_answer(messages: list[AnyMessage]) -> Answer:
    """Des messages LangChain vers une Answer du cœur, avec les sources de la dernière question."""
    last_question_index = max(i for i, message in enumerate(messages) if message.type == "human")
    tool_messages = [message for message in messages[last_question_index:] if message.type == "tool"]

    sources = {
        _source_file(document)
        for message in tool_messages
        for document in (getattr(message, "artifact", None) or [])
    }
    return Answer(messages[-1].text, tuple(sorted(sources)))


def _source_file(document: Document | dict[str, Any]) -> str:
    # Relu dans le checkpointer, un Document revient sous forme de dictionnaire
    metadata = document.metadata if isinstance(document, Document) else document["metadata"]
    return PurePath(metadata["source"]).name
