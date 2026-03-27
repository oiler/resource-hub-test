import re
import requests
from dataclasses import dataclass
from bs4 import BeautifulSoup

GOOGLE_DOC_PATTERN = re.compile(r"docs\.google\.com/document/d/([a-zA-Z0-9_-]+)")
GOOGLE_FOLDER_PATTERN = re.compile(r"drive\.google\.com/drive/folders/")


@dataclass
class FetchResult:
    url: str
    message_text: str
    content: str | None = None
    cannot_access: bool = False
    is_folder: bool = False


def fetch_content(url: str, message_text: str) -> FetchResult:
    if GOOGLE_FOLDER_PATTERN.search(url):
        return FetchResult(url=url, message_text=message_text, is_folder=True)

    doc_match = GOOGLE_DOC_PATTERN.search(url)
    if doc_match:
        return _fetch_google_doc(url, message_text, doc_match.group(1))

    return _fetch_standard_url(url, message_text)


def _fetch_google_doc(url: str, message_text: str, doc_id: str) -> FetchResult:
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    try:
        response = requests.get(export_url, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            # Login redirect — Google returned an HTML page instead of the doc
            return FetchResult(url=url, message_text=message_text, cannot_access=True)
        return FetchResult(url=url, message_text=message_text, content=response.text)
    except Exception:
        return FetchResult(url=url, message_text=message_text, cannot_access=True)


def _fetch_standard_url(url: str, message_text: str) -> FetchResult:
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        parts = []
        title = soup.find("title")
        if title:
            parts.append(title.get_text(strip=True))

        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            parts.append(meta_desc["content"])

        for p in soup.find_all("p")[:3]:
            text = p.get_text(strip=True)
            if text:
                parts.append(text)

        content = "\n".join(parts) if parts else None
        return FetchResult(url=url, message_text=message_text, content=content)
    except Exception:
        return FetchResult(url=url, message_text=message_text, cannot_access=True)
