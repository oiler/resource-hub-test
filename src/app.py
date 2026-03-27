import os
import logging
from slack_bolt import App
from notion_client import Client as NotionClient
from src.config import get_channel_ids, get_field_options, get_env
from src.fetcher import fetch_content
from src.enrichment import enrich
from src.writer import write_to_notion
from src.notifier import send_failure_alert
from src.listener import build_pipeline_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(
    token=get_env("SLACK_BOT_TOKEN"),
    signing_secret=get_env("SLACK_SIGNING_SECRET"),
    token_verification_enabled=False,
)

notion_client = NotionClient(auth=get_env("NOTION_TOKEN"))
field_options = get_field_options()
allowed_channels = get_channel_ids()


def pipeline(url: str, message_text: str, event: dict):
    logger.info(f"Processing URL: {url}")

    fetch_result = fetch_content(url, message_text)

    enriched = enrich(fetch_result, field_options)

    slack_meta = {
        "channel_id": event.get("channel", ""),
        "permalink": event.get("permalink", ""),  # Injected by listener after API call
        "user_id": event.get("user", ""),
    }

    def notifier(permalink: str, error: str):
        send_failure_alert(
            slack_client=app.client,
            permalink=permalink,
            error=error,
        )

    result = write_to_notion(
        fetch_result=fetch_result,
        enriched=enriched,
        slack_meta=slack_meta,
        notion_client=notion_client,
        notifier=notifier,
    )

    if result.success:
        logger.info(f"Successfully wrote to Notion: {url}")
    else:
        logger.error(f"Failed to write to Notion: {result.error}")


handler = build_pipeline_handler(
    allowed_channels=allowed_channels,
    pipeline=pipeline,
    notion_client=notion_client,
)

app.event("message")(handler)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.start(port=port)
