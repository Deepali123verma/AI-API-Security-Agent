import json
import re
from typing import Any

SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|authorization)\s*[:=]\s*['\"]?([^\s'\",}]+)"),
    re.compile(r"(?i)bearer\s+[a-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"),
)

MAX_TEXT_LENGTH = 2000
MAX_JSON_LENGTH = 8000


def truncate_text(value: str | None, max_length: int = MAX_TEXT_LENGTH) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3] + "..."


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def sanitize_value(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        return "[TRUNCATED]"

    if isinstance(value, str):
        return truncate_text(redact_secrets(value))

    if isinstance(value, dict):
        return {
            str(key): sanitize_value(item, depth + 1)
            for key, item in list(value.items())[:40]
        }

    if isinstance(value, list):
        return [sanitize_value(item, depth + 1) for item in value[:40]]

    if isinstance(value, (int, float, bool)) or value is None:
        return value

    return truncate_text(redact_secrets(str(value)))


def to_safe_json(data: Any) -> str:
    sanitized = sanitize_value(data)
    serialized = json.dumps(sanitized, default=str, ensure_ascii=True)
    if len(serialized) > MAX_JSON_LENGTH:
        return serialized[: MAX_JSON_LENGTH - 3] + "..."
    return serialized
