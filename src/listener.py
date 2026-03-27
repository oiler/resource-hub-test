import re
import threading
from src.config import get_env

URL_PATTERN = re.compile(r"<?(https?://[^\s|>]+)>?")


def extract_urls(text: str) -> list[str]:
    matches = URL_PATTERN.findall(text)
    return matches[:1]  # First URL only


def is_duplicate(permalink: str, notion_client) -> bool:
    shadow_db_id = get_env("NOTION_SHADOW_DB_ID")
    result = notion_client.databases.query(
        database_id=shadow_db_id,
        filter={
            "property": "Permalink",
            "rich_text": {"equals": permalink},
        },
    )
    return len(result["results"]) > 0


def build_pipeline_handler(allowed_channels: list[str], pipeline, notion_client=None):
    def handle_message(event, ack, client):
        ack()  # Acknowledge immediately — Bolt requires response within 3 seconds

        channel = event.get("channel", "")
        if channel not in allowed_channels:
            return

        text = event.get("text", "") or ""
        urls = extract_urls(text)
        if not urls:
            return

        # Fetch the permalink via the Slack API — it is not in the event payload
        ts = event.get("ts", "")
        permalink = ""
        if ts and client:
            try:
                response = client.conversations_getPermalink(channel=channel, message_ts=ts)
                permalink = response.get("permalink", "")
            except Exception:
                pass  # Non-blocking — dedup won't work but pipeline continues

        if notion_client and permalink and is_duplicate(permalink, notion_client):
            return

        enriched_event = {**event, "permalink": permalink}

        thread = threading.Thread(
            target=pipeline,
            args=(urls[0], text, enriched_event),
            daemon=True,
        )
        thread.start()

    return handle_message
