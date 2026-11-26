"""Lancer un canal : uv run --env-file .env assistant terminal

Les canaux sont déclarés dans pyproject.toml : en ajouter un ne change pas ce fichier.
"""

import argparse
import os
from importlib.metadata import entry_points

from assistant.bootstrap import build_assistant

CHANNEL_GROUP = "assistant.channels"


def main() -> None:
    channels = entry_points(group=CHANNEL_GROUP)

    parser = argparse.ArgumentParser(description="Assistant LangChain : un cœur, plusieurs canaux.")
    parser.add_argument("channel", choices=channels.names)
    run_channel = channels[parser.parse_args().channel].load()

    run_channel(build_assistant(os.environ), os.environ)


if __name__ == "__main__":
    main()
