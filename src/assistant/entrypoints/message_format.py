"""Mise en forme commune aux canaux : la réponse, puis ses sources."""

from assistant.domain.answer import ActionToApprove, Answer


def format_sources(answer: Answer) -> str:
    return f"\n\nSources : {', '.join(answer.sources)}" if answer.sources else ""


def format_answer(answer: Answer) -> str:
    return answer.text + format_sources(answer)


def format_action(action: ActionToApprove) -> str:
    lines = "\n".join(f"- {description}" for description in action.actions)
    return f"L'assistant veut exécuter :\n{lines}"
