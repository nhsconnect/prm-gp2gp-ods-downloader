import json
from logging import LogRecord, makeLogRecord, Formatter
from datetime import datetime

DEFAULT_LOG_RECORD_ATTRS = vars(makeLogRecord({})).keys()


class JsonFormatter(Formatter):
    def format(self, record: LogRecord) -> str:
        return json.dumps(
            {
                name: value
                for (name, value) in vars(record).items()
                if name not in DEFAULT_LOG_RECORD_ATTRS
            }
            | {
                "level": record.levelname,
                "message": record.msg,
                "module": record.module,
                "time": datetime.utcfromtimestamp(record.created).isoformat(),
            }
        )
