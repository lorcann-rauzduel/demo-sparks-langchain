"""Les règles des messages Discord : quand un message est une question, et la longueur maximale."""

from assistant.domain.answer import ActionToApprove, Answer
from assistant.entrypoints.message_format import format_action, format_answer

DISCORD_MAX_MESSAGE_LENGTH = 2000  # règle de la plateforme Discord


def question_from_message(content: str, bot_id: int, is_private: bool) -> str | None:
    """En message privé, tout message est une question ; sur un serveur, seulement si le bot est mentionné."""
    if is_private:
        return content

    mentions = (f"<@{bot_id}>", f"<@!{bot_id}>")
    if not any(mention in content for mention in mentions):
        return None

    for mention in mentions:
        content = content.replace(mention, "")
    return content.strip()


def split_message(text: str, max_length: int = DISCORD_MAX_MESSAGE_LENGTH) -> list[str]:
    """Découpe un message trop long pour Discord, de préférence à un retour à la ligne."""
    pieces: list[str] = []

    while len(text) > max_length:
        cut = text.rfind("\n", 0, max_length + 1)

        if cut <= 0:  # aucun retour à la ligne : on coupe à la longueur maximale
            pieces.append(text[:max_length])
            text = text[max_length:]
        else:
            pieces.append(text[:cut])
            text = text[cut + 1 :]

    return [*pieces, text]


def discord_user(discord_user_id: int) -> str:
    # Préfixe : un même numéro sur deux plateformes reste deux utilisateurs distincts
    return f"discord:{discord_user_id}"


def replies_for(result: Answer | ActionToApprove) -> list[str]:
    """Les messages à envoyer : la réponse et ses sources, ou l'action qui attend une décision."""
    if isinstance(result, ActionToApprove):
        return split_message(format_action(result))
    return split_message(format_answer(result))
