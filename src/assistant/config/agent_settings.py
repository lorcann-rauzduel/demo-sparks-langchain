"""Les réglages de l'agent : le modèle, son prompt et la façon dont il travaille."""

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from assistant.config.environment import read_setting

DEFAULT_MODEL = "groq:openai/gpt-oss-120b"
DEFAULT_SYSTEM_PROMPT_FILE = "prompts/system_prompt.md"
DEFAULT_PASSAGES_PER_SEARCH = 3
DEFAULT_SUMMARY_TRIGGER_TOKENS = 2000
DEFAULT_MESSAGES_KEPT_AFTER_SUMMARY = 4
DEFAULT_MODEL_CALL_LIMIT = 6


@dataclass(frozen=True)
class AgentSettings:
    model: str
    system_prompt_file: Path
    passages_per_search: int
    summary_trigger_tokens: int  # au-delà, les anciens messages sont résumés
    messages_kept_after_summary: int  # les derniers messages, gardés tels quels
    model_call_limit: int  # par question : au-delà, l'agent s'arrête

    @classmethod
    def from_environment(cls, environment: Mapping[str, str]) -> "AgentSettings":
        def read(name: str, default: str | int) -> str:
            return read_setting(environment, name, default)

        return cls(
            model=read("LLM_MODEL", DEFAULT_MODEL),
            system_prompt_file=Path(read("SYSTEM_PROMPT_FILE", DEFAULT_SYSTEM_PROMPT_FILE)),
            passages_per_search=int(read("PASSAGES_PER_SEARCH", DEFAULT_PASSAGES_PER_SEARCH)),
            summary_trigger_tokens=int(read("SUMMARY_TRIGGER_TOKENS", DEFAULT_SUMMARY_TRIGGER_TOKENS)),
            messages_kept_after_summary=int(
                read("MESSAGES_KEPT_AFTER_SUMMARY", DEFAULT_MESSAGES_KEPT_AFTER_SUMMARY)
            ),
            model_call_limit=int(read("MODEL_CALL_LIMIT", DEFAULT_MODEL_CALL_LIMIT)),
        )
