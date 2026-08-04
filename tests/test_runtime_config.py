import json
from pathlib import Path

from pytest import MonkeyPatch

from app.runtime_config import RUNTIME_CONFIG_PATH_ENV, get_pinned_model


def test_falls_back_to_env_var_when_no_config_file(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    missing_path = tmp_path / "does-not-exist.json"
    monkeypatch.setenv(RUNTIME_CONFIG_PATH_ENV, str(missing_path))
    monkeypatch.setenv("OLLAMA_MODEL", "llama3:8b")

    assert get_pinned_model() == "llama3:8b"


def test_config_file_overrides_env_var(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config_path = tmp_path / "runtime_config.json"
    config_path.write_text(json.dumps({"ollama_model": "qwen2.5:14b"}))
    monkeypatch.setenv(RUNTIME_CONFIG_PATH_ENV, str(config_path))
    monkeypatch.setenv("OLLAMA_MODEL", "llama3:8b")

    assert get_pinned_model() == "qwen2.5:14b"


def test_picks_up_a_live_edit_without_any_reload(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    """The whole point: editing the file is enough, no restart, no re-import."""
    config_path = tmp_path / "runtime_config.json"
    config_path.write_text(json.dumps({"ollama_model": "model-a"}))
    monkeypatch.setenv(RUNTIME_CONFIG_PATH_ENV, str(config_path))

    assert get_pinned_model() == "model-a"

    config_path.write_text(json.dumps({"ollama_model": "model-b"}))
    assert get_pinned_model() == "model-b"


def test_malformed_config_file_falls_back_instead_of_raising(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config_path = tmp_path / "runtime_config.json"
    config_path.write_text("{not valid json")
    monkeypatch.setenv(RUNTIME_CONFIG_PATH_ENV, str(config_path))
    monkeypatch.setenv("OLLAMA_MODEL", "fallback-model")

    assert get_pinned_model() == "fallback-model"


def test_config_file_missing_key_falls_back(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config_path = tmp_path / "runtime_config.json"
    config_path.write_text(json.dumps({"something_else": "irrelevant"}))
    monkeypatch.setenv(RUNTIME_CONFIG_PATH_ENV, str(config_path))
    monkeypatch.setenv("OLLAMA_MODEL", "fallback-model")

    assert get_pinned_model() == "fallback-model"


def test_config_file_blank_model_falls_back(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config_path = tmp_path / "runtime_config.json"
    config_path.write_text(json.dumps({"ollama_model": "   "}))
    monkeypatch.setenv(RUNTIME_CONFIG_PATH_ENV, str(config_path))
    monkeypatch.setenv("OLLAMA_MODEL", "fallback-model")

    assert get_pinned_model() == "fallback-model"