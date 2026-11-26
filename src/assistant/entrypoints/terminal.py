"""Canal terminal : l'utilisateur écrit dans le terminal, la réponse s'affiche en continu ou d'un bloc."""

from collections.abc import Mapping

from assistant.application.assistant import Assistant
from assistant.domain.answer import ActionToApprove, Answer
from assistant.entrypoints.message_format import format_action, format_answer, format_sources

USER_ID = "terminal"
YES = "o"


def run(assistant: Assistant, settings: Mapping[str, str]) -> None:
    # TERMINAL_STREAMING=off dans .env : la réponse s'affiche d'un bloc
    streaming = settings.get("TERMINAL_STREAMING", "on") != "off"

    print("Assistant prêt. /new pour une nouvelle conversation, ligne vide pour quitter.")
    while question := input("> ").strip():
        if streaming:
            result = _print_streamed_answer(assistant, question)
        else:
            result = assistant.answer(USER_ID, question)
            if isinstance(result, Answer):
                print(format_answer(result))

        # Validation humaine : l'agent est en pause tant que l'utilisateur n'a pas décidé
        while isinstance(result, ActionToApprove):
            print(format_action(result))
            approved = input(f"Valider ? ({YES}/n) ").strip().lower() == YES
            result = assistant.decide(USER_ID, approved)
            if isinstance(result, Answer):
                print(format_answer(result))


def _print_streamed_answer(assistant: Assistant, question: str) -> Answer | ActionToApprove:
    has_streamed = False

    for piece in assistant.stream(USER_ID, question):
        if isinstance(piece, ActionToApprove):
            if has_streamed:
                print()
            return piece
        if isinstance(piece, Answer):
            # La réponse complète arrive en dernier : il ne reste que ses sources à afficher,
            # sauf si le cœur a répondu sans le modèle, donc sans flux
            print(format_sources(piece) if has_streamed else piece.text, flush=True)
            return piece
        print(piece.text, end="", flush=True)
        has_streamed = True

    raise RuntimeError("The stream ended without a complete answer.")
