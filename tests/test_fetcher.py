import responses as responses_mock
import pytest
from src.fetcher import fetch_content, FetchResult


@responses_mock.activate
def test_google_doc_uses_export_url():
    doc_url = "https://docs.google.com/document/d/abc123/edit"
    export_url = "https://docs.google.com/document/d/abc123/export?format=txt"
    responses_mock.add(responses_mock.GET, export_url, body="Doc content here", status=200)

    result = fetch_content(doc_url, "check out this doc")

    assert result.content == "Doc content here"
    assert result.cannot_access is False
    assert result.is_folder is False


@responses_mock.activate
def test_google_doc_login_redirect_sets_cannot_access():
    doc_url = "https://docs.google.com/document/d/abc123/edit"
    export_url = "https://docs.google.com/document/d/abc123/export?format=txt"
    # Google returns HTML login page instead of doc content
    responses_mock.add(responses_mock.GET, export_url, body="<html>Sign in</html>", status=200,
                       content_type="text/html")

    result = fetch_content(doc_url, "check out this doc")

    assert result.cannot_access is True
    assert result.content is None


def test_google_drive_folder_sets_folder_flag():
    folder_url = "https://drive.google.com/drive/folders/xyz789"
    result = fetch_content(folder_url, "here is our folder")

    assert result.is_folder is True
    assert result.cannot_access is False
    assert result.content is None
    assert result.message_text == "here is our folder"


@responses_mock.activate
def test_standard_url_extracts_title_and_description():
    url = "https://example.com/article"
    html = """
    <html>
      <head>
        <title>Test Article</title>
        <meta name="description" content="A great article about testing.">
      </head>
      <body><p>First paragraph content.</p></body>
    </html>
    """
    responses_mock.add(responses_mock.GET, url, body=html, status=200, content_type="text/html")

    result = fetch_content(url, "interesting article")

    assert "Test Article" in result.content
    assert "A great article about testing." in result.content
    assert result.cannot_access is False


@responses_mock.activate
def test_failed_fetch_sets_cannot_access():
    url = "https://example.com/dead-link"
    responses_mock.add(responses_mock.GET, url, status=404)

    result = fetch_content(url, "broken link")

    assert result.cannot_access is True
    assert result.content is None
    assert result.url == url
    assert result.message_text == "broken link"


@responses_mock.activate
def test_timeout_sets_cannot_access():
    import requests
    url = "https://example.com/slow"
    responses_mock.add(responses_mock.GET, url, body=requests.exceptions.Timeout())

    result = fetch_content(url, "slow page")

    assert result.cannot_access is True
