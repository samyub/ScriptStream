import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.errors import StorageError

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "research_history.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)


def load_history() -> list[dict]:
    _ensure_data_dir()
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_record(record: dict) -> str:
    _ensure_data_dir()
    record_id = str(uuid.uuid4())
    record["id"] = record_id
    record["created_at"] = datetime.now(timezone.utc).isoformat()

    history = load_history()
    history.append(record)

    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2, default=str)
    except Exception as e:
        raise StorageError(f"Failed to write history: {e}")

    return record_id


def get_record_by_id(record_id: str) -> Optional[dict]:
    history = load_history()
    for record in history:
        if record.get("id") == record_id:
            return record
    return None


def get_all_records() -> list[dict]:
    return load_history()
