import json
from logging import makeLogRecord

from prmods.io.logging import JsonFormatter


def test_json_formatter_correctly_formats_record():

    record = makeLogRecord(
        {
            "levelname": "warning",
            "msg": "a message",
            "created": 1607965513.358049,
            "extra_field": "some_value",
        }
    )

    expected = {
        "level": "warning",
        "message": "a message",
        "time": "2020-12-14T17:05:13.358049",
        "extra_field": "some_value",
    }

    actual_json_string = JsonFormatter().format(record)
    actual = json.loads(actual_json_string)

    assert actual == expected
