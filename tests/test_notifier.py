from unittest.mock import MagicMock, patch
from src.notifier import send_failure_alert


def test_send_failure_alert_calls_slack():
    mock_client = MagicMock()
    with patch("src.notifier.get_env", return_value="C_OPS_123"):
        send_failure_alert(
            slack_client=mock_client,
            permalink="https://ajp.slack.com/archives/C123/p123456",
            error="Notion API timeout",
        )

    mock_client.chat_postMessage.assert_called_once()
    call_kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert call_kwargs["channel"] == "C_OPS_123"
    assert "https://ajp.slack.com/archives/C123/p123456" in call_kwargs["text"]
    assert "Notion API timeout" in call_kwargs["text"]
