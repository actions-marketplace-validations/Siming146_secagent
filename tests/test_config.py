"""Test configuration loading."""

import os
from secagent.config import Settings, get_settings


def test_default_settings():
    settings = Settings()
    assert settings.deepseek_base_url == "https://api.deepseek.com"
    assert settings.deepseek_chat_model == "deepseek-v4-flash"
    assert settings.deepseek_reasoner_model == "deepseek-v4-pro"
    assert settings.sandbox_timeout_seconds == 60


def test_env_override(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_CHAT_MODEL", "custom-model")
    monkeypatch.setenv("SANDBOX_TIMEOUT_SECONDS", "120")
    settings = Settings()
    assert settings.deepseek_chat_model == "custom-model"
    assert settings.sandbox_timeout_seconds == 120
