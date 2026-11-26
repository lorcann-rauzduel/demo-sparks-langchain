"""Canal Discord : une application avec un bot (un webhook ne sait pas lire les messages)."""

import asyncio
from collections.abc import Mapping

import discord

from assistant.application.assistant import Assistant
from assistant.entrypoints.discord_bot.approval import send_result
from assistant.entrypoints.discord_bot.messages import discord_user, question_from_message


def run(assistant: Assistant, settings: Mapping[str, str]) -> None:
    # Intents par défaut : Discord donne le texte des messages privés et des mentions du bot,
    # sans l'intent privilégié Message Content
    client = discord.Client(intents=discord.Intents.default())

    @client.event
    async def on_ready() -> None:
        print(f"Bot Discord connecté : {client.user}. Ctrl+C pour arrêter.", flush=True)

    @client.event
    async def on_message(message: discord.Message) -> None:
        if client.user is None or message.author.bot:
            return

        is_private = isinstance(message.channel, discord.DMChannel)
        question = question_from_message(message.content, client.user.id, is_private)
        if question is None:
            return

        async with message.channel.typing():
            # Le cas d'usage est synchrone : on l'exécute hors de la boucle d'événements du bot
            result = await asyncio.to_thread(assistant.answer, discord_user(message.author.id), question)

        await send_result(message.channel.send, assistant, message.author.id, result)

    client.run(settings["DISCORD_TOKEN"])
