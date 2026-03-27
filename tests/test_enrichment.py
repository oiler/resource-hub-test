import pytest
from unittest.mock import patch, MagicMock
from src.fetcher import FetchResult
from src.enrichment import enrich, EnrichedItem


MOCK_OPTIONS = {
    "type": ["Article", "Video", "Tool"],
    "category": ["Fundraising", "Communications"],
    "role": ["Executive Director", "Development Staff"],
    "action": ["Read", "Watch", "Use"],
    "subcategory": ["Grants", "Major Gifts"],
}


def _make_fetch_result(content="Page content", cannot_access=False, is_folder=False):
    return FetchResult(
        url="https://example.com",
        message_text="great resource for EDs",
        content=content,
        cannot_access=cannot_access,
        is_folder=is_folder,
    )


def test_enrich_returns_enriched_item():
    mock_response = EnrichedItem(
        resource="Test Resource",
        description="A useful resource for executive directors.",
        type="Article",
        category="Fundraising",
        role="Executive Director",
        action="Read",
        subcategory="Grants",
    )
    with patch("src.enrichment.client.chat.completions.create", return_value=mock_response):
        result = enrich(_make_fetch_result(), MOCK_OPTIONS)

    assert result.resource == "Test Resource"
    assert result.type == "Article"
    assert result.category == "Fundraising"


def test_enrich_nulls_invalid_select_value():
    mock_response = EnrichedItem(
        resource="Test Resource",
        description="A useful resource.",
        type="InvalidType",  # Not in MOCK_OPTIONS
        category="Fundraising",
        role=None,
        action=None,
        subcategory=None,
    )
    with patch("src.enrichment.client.chat.completions.create", return_value=mock_response):
        result = enrich(_make_fetch_result(), MOCK_OPTIONS)

    assert result.type is None  # Nulled out by validator


def test_enrich_cannot_access_item():
    mock_response = EnrichedItem(
        resource="Unknown Resource",
        description="Content could not be accessed.",
        type=None,
        category=None,
        role=None,
        action=None,
        subcategory=None,
    )
    with patch("src.enrichment.client.chat.completions.create", return_value=mock_response):
        result = enrich(_make_fetch_result(cannot_access=True), MOCK_OPTIONS)

    assert result.resource is not None


def test_enrich_folder_item():
    mock_response = EnrichedItem(
        resource="Resource Folder",
        description="This link points to a folder containing multiple documents.",
        type=None,
        category=None,
        role=None,
        action=None,
        subcategory=None,
    )
    with patch("src.enrichment.client.chat.completions.create", return_value=mock_response):
        result = enrich(_make_fetch_result(is_folder=True), MOCK_OPTIONS)

    assert result is not None
