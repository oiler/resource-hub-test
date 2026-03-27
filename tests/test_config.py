import os
import pytest
from unittest.mock import patch


def test_config_loads_channel_ids():
    with patch.dict(os.environ, {"SLACK_CHANNEL_IDS": "C123,C456"}):
        from src.config import get_channel_ids
        assert get_channel_ids() == ["C123", "C456"]


def test_config_loads_single_channel():
    with patch.dict(os.environ, {"SLACK_CHANNEL_IDS": "C123"}):
        from src.config import get_channel_ids
        assert get_channel_ids() == ["C123"]


def test_field_options_loads():
    from src.config import get_field_options
    options = get_field_options()
    assert "type" in options
    assert "category" in options
    assert "role" in options
    assert "action" in options
    assert "subcategory" in options
    assert isinstance(options["type"], list)


def test_field_options_not_empty():
    from src.config import get_field_options
    options = get_field_options()
    for field, values in options.items():
        assert len(values) > 0, f"Field '{field}' has no options"
