from __future__ import annotations

import re
from typing import Any

from app.models.finding import Finding


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_title(title: str | None) -> str:
    if not title:
        return ""
    return _WHITESPACE_RE.sub(" ", title.strip().lower())


def normalize_category(category: str | None) -> str:
    if not category:
        return ""
    return category.strip().lower()


def normalize_method(method: str | None) -> str:
    if not method:
        return ""
    return method.strip().upper()


def normalize_path(path: str | None) -> str:
    if not path:
        return ""
    value = path.strip()
    if len(value) > 1 and value.endswith("/"):
        value = value.rstrip("/")
    return value


def extract_method_path(finding: Finding) -> tuple[str | None, str | None]:
    if finding.endpoint is not None:
        return finding.endpoint.method, finding.endpoint.path

    structured = finding.structured_evidence or {}
    method = structured.get("method")
    path = structured.get("path")
    if isinstance(method, str) or isinstance(path, str):
        return (
            method if isinstance(method, str) else None,
            path if isinstance(path, str) else None,
        )

    endpoint_label = structured.get("endpoint")
    if isinstance(endpoint_label, str) and " " in endpoint_label:
        method_part, path_part = endpoint_label.split(" ", 1)
        return method_part, path_part
    return None, None


def finding_fingerprint(finding: Finding) -> str:
    """Deterministic identity key for cross-scan regression matching.

    Uses category + normalized title + HTTP method + path.
    Does not use database IDs or AI fields.
    """
    method, path = extract_method_path(finding)
    return "|".join(
        [
            normalize_category(finding.category),
            normalize_title(finding.title),
            normalize_method(method),
            normalize_path(path),
        ]
    )


def safe_text(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def truncate_text(value: str, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."
