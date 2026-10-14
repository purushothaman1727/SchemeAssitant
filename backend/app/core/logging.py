import json
import logging
import sys
from datetime import datetime, timezone

# Fields that must never reach logs (disability details, income, identifiers).
_SENSITIVE_KEYS = {
    "disability",
    "disability_type",
    "disability_percentage",
    "udid_status",
    "certificate_status",
    "income",
    "annual_income",
    "date_of_birth",
    "password",
    "token",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra = getattr(record, "ctx", None)
        if isinstance(extra, dict):
            payload.update({k: v for k, v in extra.items() if k not in _SENSITIVE_KEYS})
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    for noisy in ("httpx", "httpcore"):  # outbound request lines can carry query strings
        logging.getLogger(noisy).setLevel(logging.WARNING)
