"""La validation humaine sur Discord : deux boutons sous l'action proposée, Valider et Refuser."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import discord

from assistant.application.assistant import Assistant
from assistant.domain.answer import ActionToApprove, Answer
from assistant.entrypoints.discord_bot.messages import discord_user, replies_for

APPROVAL_TIMEOUT_SECONDS = 600  # par défaut, Discord.py désactive les boutons au bout de 180 secondes

Send = Callable[..., Awaitable[Any]]


async def send_result(
    send: Send, assistant: Assistant, requester_id: int, result: Answer | ActionToApprove
) -> None:
    """Envoie la réponse, ou l'action à valider avec ses boutons sous le dernier message."""
    *replies, last = replies_for(result)
    for reply in replies:
        await send(reply)

    if isinstance(result, ActionToApprove):
        await send(last, view=ApprovalView(assistant, requester_id))
    else:
        await send(last)


class ApprovalView(discord.ui.View):
    def __init__(self, assistant: Assistant, requester_id: int) -> None:
        super().__init__(timeout=APPROVAL_TIMEOUT_SECONDS)
        self._assistant = assistant
        self._requester_id = requester_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Dans un salon, tout le monde voit les boutons : seul l'auteur de la demande décide
        if interaction.user.id == self._requester_id:
            return True
        await interaction.response.send_message("Seul l'auteur de la demande peut décider.", ephemeral=True)
        return False

    @discord.ui.button(label="Valider", style=discord.ButtonStyle.success)
    async def approve(
        self, interaction: discord.Interaction, button: discord.ui.Button["ApprovalView"]
    ) -> None:
        await self._decide(interaction, approved=True)

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.danger)
    async def reject(
        self, interaction: discord.Interaction, button: discord.ui.Button["ApprovalView"]
    ) -> None:
        await self._decide(interaction, approved=False)

    async def _decide(self, interaction: discord.Interaction, approved: bool) -> None:
        # Discord attend une réponse au clic en moins de 3 secondes : on désactive d'abord les boutons,
        # ce qui répond au clic et empêche un second clic, puis l'agent reprend
        self.stop()
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await interaction.response.edit_message(view=self)

        result = await asyncio.to_thread(self._assistant.decide, discord_user(self._requester_id), approved)
        # Après la réponse au clic, les messages suivants partent par le suivi de l'interaction
        await send_result(interaction.followup.send, self._assistant, self._requester_id, result)
