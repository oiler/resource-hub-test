from dataclasses import dataclass
from notion_client import Client
from src.fetcher import FetchResult
from src.enrichment import EnrichedItem
from src.config import get_env


@dataclass
class WriteResult:
    success: bool
    error: str | None = None


def write_to_notion(
    fetch_result: FetchResult,
    enriched: EnrichedItem,
    slack_meta: dict,
    notion_client,
    notifier,
) -> WriteResult:
    shadow_db_id = get_env("NOTION_SHADOW_DB_ID")
    production_db_id = get_env("NOTION_PRODUCTION_DB_ID")

    flags = []
    if fetch_result.cannot_access:
        flags.append("cannot_access")
    if fetch_result.is_folder:
        flags.append("folder_link")
    notes = ", ".join(flags) if flags else ""

    # Shadow write first
    try:
        notion_client.pages.create(
            parent={"database_id": shadow_db_id},
            properties=_build_shadow_properties(fetch_result, slack_meta, notes),
        )
    except Exception as e:
        notifier(
            permalink=slack_meta["permalink"],
            error=f"Shadow write failed: {e}",
        )
        return WriteResult(success=False, error=str(e))

    # Production write second
    try:
        notion_client.pages.create(
            parent={"database_id": production_db_id},
            properties=_build_production_properties(fetch_result, enriched),
        )
    except Exception as e:
        notifier(
            permalink=slack_meta["permalink"],
            error=f"Production write failed: {e}",
        )
        return WriteResult(success=False, error=str(e))

    return WriteResult(success=True)


def _build_shadow_properties(fetch_result: FetchResult, slack_meta: dict, notes: str) -> dict:
    props = {
        "URL": {"url": fetch_result.url},
        "Message": {"rich_text": [{"text": {"content": fetch_result.message_text or ""}}]},
        "Channel ID": {"rich_text": [{"text": {"content": slack_meta["channel_id"]}}]},
        "Permalink": {"rich_text": [{"text": {"content": slack_meta["permalink"]}}]},
        "User ID": {"rich_text": [{"text": {"content": slack_meta["user_id"]}}]},
        "Status": {"select": {"name": "success"}},
        "Notes": {"rich_text": [{"text": {"content": notes}}]},
    }
    return props


def _build_production_properties(fetch_result: FetchResult, enriched: EnrichedItem) -> dict:
    props = {
        "Resource": {"title": [{"text": {"content": enriched.resource or fetch_result.url}}]},
        "URL": {"url": fetch_result.url},
        "Description": {"rich_text": [{"text": {"content": enriched.description or ""}}]},
        "Status": {"select": {"name": "Needs Review"}},
    }
    for field_name in ("type", "category", "role", "action", "subcategory"):
        value = getattr(enriched, field_name)
        notion_key = field_name.capitalize()
        if value:
            props[notion_key] = {"select": {"name": value}}
    return props
