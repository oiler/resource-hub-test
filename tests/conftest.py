import os
import pytest


@pytest.fixture(autouse=True)
def set_required_env_vars(monkeypatch):
    """Set required environment variables for all unit tests."""
    monkeypatch.setenv("LITELLM_MODEL", "anthropic/claude-3-5-haiku-20241022")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
    monkeypatch.setenv("SLACK_CHANNEL_IDS", "C123456")
    monkeypatch.setenv("NOTION_TOKEN", "secret_test")
    monkeypatch.setenv("NOTION_DATABASE_ID", "test-db-id")
