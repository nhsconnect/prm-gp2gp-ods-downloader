import json
from datetime import datetime
from pathlib import Path


def _serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} is not JSON serializable")


def write_json_file(content: dict, file_path: str):
    json_string = json.dumps(content, default=_serialize_datetime)
    path = Path(file_path)
    path.write_text(json_string)


def read_json_file(file_path: str) -> dict:
    path = Path(file_path)
    json_string = path.read_text()
    return json.loads(json_string)


def upload_json_object(s3_obj, string):
    body = bytes(json.dumps(string, default=_serialize_datetime).encode("UTF-8"))
    s3_obj.put(Body=body, ContentType="application/json")
