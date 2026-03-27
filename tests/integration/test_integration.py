import os
import pytest

REQUIRED_VARS = [
    "SLACK_BOT_TOKEN",
    "SLACK_SIGNING_SECRET",
    "LLM_API_KEY",
    "LITELLM_MODEL",
    "NOTION_TOKEN",
    "NOTION_PRODUCTION_DB_ID",
    "NOTION_SHADOW_DB_ID",
]

skip_if_no_credentials = pytest.mark.skipif(
    not all(os.environ.get(v) for v in REQUIRED_VARS),
    reason="Integration tests require real API credentials in environment",
)


@skip_if_no_credentials
def test_google_doc_fetch_live():
    """Fetches a known public Google Doc and checks content is returned."""
    from src.fetcher import fetch_content

    # Replace with a real public Google Doc URL for your workspace
    PUBLIC_DOC_URL = os.environ.get("TEST_PUBLIC_DOC_URL", "")
    if not PUBLIC_DOC_URL:
        pytest.skip("TEST_PUBLIC_DOC_URL not set")
    result = fetch_content(PUBLIC_DOC_URL, "test message")
    assert result.content is not None
    assert result.cannot_access is False


@skip_if_no_credentials
def test_llm_enrichment_live():
    """Calls the real LLM API and checks that a valid EnrichedItem is returned."""
    from src.fetcher import FetchResult
    from src.enrichment import enrich
    from src.config import get_field_options

    fetch_result = FetchResult(
        url="https://www.councilofnonprofits.org/running-nonprofit/fundraising",
        message_text="Great fundraising guide for EDs",
        content="Fundraising guide for nonprofit executive directors covering major gifts, grants, and annual campaigns.",
    )
    enriched = enrich(fetch_result, get_field_options())
    assert enriched.resource is not None
    assert enriched.description is not None


@skip_if_no_credentials
def test_notion_shadow_write_live():
    """Writes a test record to the shadow database and verifies it was created."""
    from notion_client import Client
    from src.config import get_env
    from src.fetcher import FetchResult
    from src.enrichment import EnrichedItem
    from src.writer import write_to_notion

    notion = Client(auth=get_env("NOTION_TOKEN"))
    fetch_result = FetchResult(
        url="https://example.com/integration-test",
        message_text="integration test message",
        content="test content",
    )
    enriched = EnrichedItem(
        resource="Integration Test Resource",
        description="This is an automated integration test entry. Safe to delete.",
    )
    slack_meta = {
        "channel_id": "TEST",
        "permalink": "https://slack.com/test-permalink",
        "user_id": "TEST_USER",
    }
    result = write_to_notion(
        fetch_result=fetch_result,
        enriched=enriched,
        slack_meta=slack_meta,
        notion_client=notion,
        notifier=lambda **kwargs: None,
    )
    assert result.success is True
