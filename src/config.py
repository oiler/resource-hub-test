import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_FIELD_OPTIONS_PATH = Path(__file__).parent.parent / "field_options.json"


def get_channel_ids() -> list[str]:
    raw = os.environ["SLACK_CHANNEL_IDS"]
    return [ch.strip() for ch in raw.split(",") if ch.strip()]


def get_field_options() -> dict[str, list[str]]:
    with open(_FIELD_OPTIONS_PATH) as f:
        return json.load(f)


def get_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value
