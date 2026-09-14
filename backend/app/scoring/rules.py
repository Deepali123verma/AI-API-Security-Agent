"""Deterministic risk scoring rules.

Base severity weights (starting values, not random):
    CRITICAL = 90
    HIGH     = 75
    MEDIUM   = 50
    LOW      = 25
    INFO     = 10

Risk level thresholds (derived from final score):
    90-100 -> CRITICAL
    70-89  -> HIGH
    40-69  -> MEDIUM
    20-39  -> LOW
    0-19   -> INFO
"""

BASE_SEVERITY_SCORES: dict[str, int] = {
    "CRITICAL": 90,
    "HIGH": 75,
    "MEDIUM": 50,
    "LOW": 25,
    "INFO": 10,
}

CONFIDENCE_ADJUSTMENTS: dict[str, int] = {
    "HIGH": 10,
    "MEDIUM": 5,
    "LOW": 0,
}

ENDPOINT_SENSITIVITY_HIGH_TERMS = ("/admin",)
ENDPOINT_SENSITIVITY_MEDIUM_TERMS = (
    "/users",
    "/accounts",
    "/profile",
    "/orders",
    "/payments",
    "/password",
    "/settings",
)

STATE_CHANGING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

AUTHORIZATION_CATEGORIES = frozenset({"Authorization"})
AUTHENTICATION_CATEGORIES = frozenset({"Authentication"})
SENSITIVE_DATA_CATEGORIES = frozenset({"Sensitive Data"})

# Overall scan score: highest finding score plus capped contribution from others.
ADDITIONAL_FINDING_WEIGHT = 0.15
ADDITIONAL_FINDING_MAX_EACH = 8
ADDITIONAL_FINDING_TOTAL_CAP = 20


def clamp_score(score: int) -> int:
    return min(100, max(0, score))


def score_to_risk_level(score: int) -> str:
    clamped = clamp_score(score)
    if clamped >= 90:
        return "CRITICAL"
    if clamped >= 70:
        return "HIGH"
    if clamped >= 40:
        return "MEDIUM"
    if clamped >= 20:
        return "LOW"
    return "INFO"
