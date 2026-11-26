from pathlib import Path

from assistant.config.agent_settings import DEFAULT_MODEL, AgentSettings


def test_without_environment_the_documented_default_model_applies() -> None:
    assert AgentSettings.from_environment({}).model == DEFAULT_MODEL


def test_the_environment_chooses_the_model_and_the_prompt_file() -> None:
    settings = AgentSettings.from_environment(
        {"LLM_MODEL": "ollama:qwen3.5:0.8b", "SYSTEM_PROMPT_FILE": "prompts/other.md"}
    )

    assert settings.model == "ollama:qwen3.5:0.8b"
    assert settings.system_prompt_file == Path("prompts/other.md")
