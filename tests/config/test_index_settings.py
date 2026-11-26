from pathlib import Path

from assistant.config.index_settings import IndexSettings


def test_the_index_settings_come_from_the_environment() -> None:
    settings = IndexSettings.from_environment({"INDEX_DIR": "other_index", "CHUNK_SIZE": "800"})

    assert settings.index_dir == Path("other_index")
    assert settings.chunk_size == 800
