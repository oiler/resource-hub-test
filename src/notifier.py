from src.config import get_env


def send_failure_alert(slack_client, permalink: str, error: str) -> None:
    ops_channel = get_env("SLACK_OPS_CHANNEL_ID")
    slack_client.chat_postMessage(
        channel=ops_channel,
        text=f":warning: Failed to process resource link.\n*Message:* {permalink}\n*Error:* {error}",
    )
