import json
from datetime import datetime
from pathlib import Path


def _serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} is not JSON serializable")


def read_json_file(file_path: str) -> dict:
    path = Path(file_path)
    json_string = path.read_text()
    return json.loads(json_string)
