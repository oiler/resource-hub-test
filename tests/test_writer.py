import pytest
from unittest.mock import MagicMock, patch, call
from src.fetcher import FetchResult
from src.enrichment import EnrichedItem
from src.writer import write_to_notion, WriteResult


def _make_inputs(cannot_access=False, is_folder=False):
    fetch_result = FetchResult(
        url="https://example.com",
        message_text="great resource",
        content="Some content",
        cannot_access=cannot_access,
        is_folder=is_folder,
    )
    enriched = EnrichedItem(
        resource="Test Resource",
        description="A useful resource.",
        type="Article",
        category="Fundraising",
        role="Executive Director",
        action="Read",
        subcategory="Grants",
    )
    slack_meta = {
        "channel_id": "C123",
        "permalink": "https://slack.com/p123",
        "user_id": "U456",
    }
    return fetch_result, enriched, slack_meta


def test_shadow_written_before_production():
    mock_notion = MagicMock()
    mock_notifier = MagicMock()
    call_order = []
    mock_notion.pages.create.side_effect = lambda **kwargs: call_order.append(
        kwargs["parent"]["database_id"]
    ) or {"id": "page-id"}

    with patch("src.writer.get_env", side_effect=lambda k: {"NOTION_SHADOW_DB_ID": "SHADOW", "NOTION_PRODUCTION_DB_ID": "PROD"}[k]):
        result = write_to_notion(*_make_inputs(), notion_client=mock_notion, notifier=mock_notifier)

    assert call_order[0] == "SHADOW"
    assert call_order[1] == "PROD"
    assert result.success is True


def test_shadow_failure_aborts_production_and_notifies():
    mock_notion = MagicMock()
    mock_notifier = MagicMock()
    mock_notion.pages.create.side_effect = Exception("Notion error")

    with patch("src.writer.get_env", side_effect=lambda k: {"NOTION_SHADOW_DB_ID": "SHADOW", "NOTION_PRODUCTION_DB_ID": "PROD"}[k]):
        result = write_to_notion(*_make_inputs(), notion_client=mock_notion, notifier=mock_notifier)

    assert result.success is False
    mock_notifier.assert_called_once()
    # Only one call to pages.create — shadow failed, production never attempted
    assert mock_notion.pages.create.call_count == 1


def test_production_failure_notifies_but_preserves_shadow():
    mock_notion = MagicMock()
    mock_notifier = MagicMock()
    call_count = [0]

    def create_side_effect(**kwargs):
        call_count[0] += 1
        if call_count[0] == 2:  # Second call (production) fails
            raise Exception("Production write failed")
        return {"id": "page-id"}

    mock_notion.pages.create.side_effect = create_side_effect

    with patch("src.writer.get_env", side_effect=lambda k: {"NOTION_SHADOW_DB_ID": "SHADOW", "NOTION_PRODUCTION_DB_ID": "PROD"}[k]):
        result = write_to_notion(*_make_inputs(), notion_client=mock_notion, notifier=mock_notifier)

    assert result.success is False
    assert mock_notion.pages.create.call_count == 2  # Both attempted
    mock_notifier.assert_called_once()


def test_cannot_access_flag_written_to_shadow():
    mock_notion = MagicMock()
    mock_notifier = MagicMock()
    mock_notion.pages.create.return_value = {"id": "page-id"}
    shadow_call_kwargs = []
    mock_notion.pages.create.side_effect = lambda **kwargs: shadow_call_kwargs.append(kwargs) or {"id": "page-id"}

    with patch("src.writer.get_env", side_effect=lambda k: {"NOTION_SHADOW_DB_ID": "SHADOW", "NOTION_PRODUCTION_DB_ID": "PROD"}[k]):
        write_to_notion(*_make_inputs(cannot_access=True), notion_client=mock_notion, notifier=mock_notifier)

    shadow_props = shadow_call_kwargs[0]["properties"]
    notes = shadow_props.get("Notes", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")
    assert "cannot_access" in notes
