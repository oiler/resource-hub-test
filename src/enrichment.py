import litellm
import instructor
from typing import ClassVar
from pydantic import BaseModel
from src.fetcher import FetchResult
from src.config import get_env

client = instructor.from_litellm(litellm.completion)

_SELECT_FIELDS = ("type", "category", "role", "action", "subcategory")


class EnrichedItem(BaseModel):
    resource: str | None = None
    description: str | None = None
    type: str | None = None
    category: str | None = None
    role: str | None = None
    action: str | None = None
    subcategory: str | None = None

    # ClassVar keeps this out of the Pydantic schema entirely
    _allowed_options: ClassVar[dict] = {}


def _apply_field_options(item: EnrichedItem, field_options: dict) -> EnrichedItem:
    """Null out any select field values not in the allowed list.

    This runs explicitly after receiving the LLM response so the check
    is guaranteed regardless of when the EnrichedItem was constructed
    (the model_validator only runs at construction time).
    """
    for field_name in _SELECT_FIELDS:
        value = getattr(item, field_name)
        allowed = field_options.get(field_name, [])
        if value and allowed and value not in allowed:
            setattr(item, field_name, None)
    return item


def enrich(fetch_result: FetchResult, field_options: dict) -> EnrichedItem:
    EnrichedItem._allowed_options = field_options

    content_section = (
        "Content could not be accessed."
        if fetch_result.cannot_access
        else (
            "This link points to a folder with multiple documents. No content was fetched."
            if fetch_result.is_folder
            else fetch_result.content or "No content available."
        )
    )

    options_text = "\n".join(
        f"- {field}: {', '.join(values)}"
        for field, values in field_options.items()
    )

    prompt = f"""You are processing a resource link for a nonprofit grantee Resource Hub.

Slack message context: {fetch_result.message_text}
URL: {fetch_result.url}
Page content:
{content_section}

Extract the following fields. For select fields, you MUST choose from the allowed values below or return null.

Allowed values:
{options_text}

Fields to extract:
- resource: The title of the resource (string)
- description: 2-3 sentences summarizing what this resource is and who it helps (string)
- type: What kind of resource this is (select)
- category: The primary topic area (select)
- role: The staff role most likely to use this (select)
- action: What the user does with this resource (select)
- subcategory: A more specific topic (select)

Return null for any select field you cannot confidently determine."""

    result = client.chat.completions.create(
        model=get_env("LITELLM_MODEL"),
        messages=[{"role": "user", "content": prompt}],
        response_model=EnrichedItem,
        max_retries=2,
    )

    return _apply_field_options(result, field_options)
