import pytest
from unittest.mock import MagicMock, patch, call
from src.listener import extract_urls, is_duplicate, build_pipeline_handler


def test_extract_urls_from_plain_url():
    text = "Check this out https://example.com great resource"
    assert extract_urls(text) == ["https://example.com"]


def test_extract_urls_strips_slack_angle_brackets():
    text = "Check this out <https://example.com|example.com>"
    assert extract_urls(text) == ["https://example.com"]


def test_extract_urls_returns_empty_for_no_url():
    text = "Hey everyone, happy Monday!"
    assert extract_urls(text) == []


def test_extract_urls_returns_first_url_only():
    text = "Two links https://example.com and https://another.com"
    urls = extract_urls(text)
    assert len(urls) == 1
    assert urls[0] == "https://example.com"


def test_is_duplicate_returns_true_when_permalink_found():
    mock_notion = MagicMock()
    mock_notion.databases.query.return_value = {
        "results": [{"id": "existing-page"}]
    }
    with patch("src.listener.get_env", return_value="SHADOW_DB"):
        assert is_duplicate("https://slack.com/p123", mock_notion) is True


def test_is_duplicate_returns_false_when_not_found():
    mock_notion = MagicMock()
    mock_notion.databases.query.return_value = {"results": []}
    with patch("src.listener.get_env", return_value="SHADOW_DB"):
        assert is_duplicate("https://slack.com/p999", mock_notion) is False


def test_handler_ignores_wrong_channel():
    pipeline = MagicMock()
    handler = build_pipeline_handler(
        allowed_channels=["C_ALLOWED"],
        pipeline=pipeline,
    )
    handler({"channel": "C_OTHER", "text": "https://example.com", "ts": "123"}, MagicMock(), MagicMock())
    pipeline.assert_not_called()


def test_handler_ignores_message_without_url():
    pipeline = MagicMock()
    handler = build_pipeline_handler(
        allowed_channels=["C_ALLOWED"],
        pipeline=pipeline,
    )
    handler({"channel": "C_ALLOWED", "text": "No links here", "ts": "123"}, MagicMock(), MagicMock())
    pipeline.assert_not_called()


def test_handler_calls_pipeline_for_valid_message():
    pipeline = MagicMock()
    mock_notion = MagicMock()
    mock_notion.databases.query.return_value = {"results": []}
    mock_slack_client = MagicMock()
    mock_slack_client.conversations_getPermalink.return_value = {
        "permalink": "https://slack.com/p123"
    }

    with patch("src.listener.get_env", return_value="SHADOW_DB"), \
         patch("src.listener.threading.Thread") as mock_thread:
        handler = build_pipeline_handler(
            allowed_channels=["C_ALLOWED"],
            pipeline=pipeline,
            notion_client=mock_notion,
        )
        handler(
            {"channel": "C_ALLOWED", "text": "https://example.com great resource", "ts": "123"},
            MagicMock(),
            mock_slack_client,
        )
        mock_thread.assert_called_once()


def test_handler_calls_ack_immediately():
    pipeline = MagicMock()
    mock_ack = MagicMock()

    handler = build_pipeline_handler(
        allowed_channels=["C_ALLOWED"],
        pipeline=pipeline,
    )
    handler({"channel": "C_OTHER", "text": "no url", "ts": "123"}, mock_ack, MagicMock())
    mock_ack.assert_called_once()
