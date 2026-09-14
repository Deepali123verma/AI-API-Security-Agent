from app.scanner.models import ScannerFinding
from app.scoring.engine import RiskScoringEngine
from app.scoring.rules import BASE_SEVERITY_SCORES, clamp_score, score_to_risk_level
from tests.scanner_helpers import make_endpoint


def _finding(**kwargs) -> ScannerFinding:
    defaults = {
        "title": "Test Finding",
        "description": "Test description",
        "severity": "MEDIUM",
        "category": "Authentication",
        "evidence": "No security requirement is defined for this operation: GET /users",
        "remediation": "Require authentication",
        "confidence": "HIGH",
    }
    defaults.update(kwargs)
    return ScannerFinding(**defaults)


def test_base_severity_scores() -> None:
    assert BASE_SEVERITY_SCORES["CRITICAL"] == 90
    assert BASE_SEVERITY_SCORES["HIGH"] == 75
    assert BASE_SEVERITY_SCORES["MEDIUM"] == 50
    assert BASE_SEVERITY_SCORES["LOW"] == 25
    assert BASE_SEVERITY_SCORES["INFO"] == 10


def test_score_bounds_never_exceed_100_or_fall_below_0() -> None:
    engine = RiskScoringEngine()
    endpoint = make_endpoint(
        1,
        "/admin/users/{id}",
        method="DELETE",
        security_defined=False,
    )
    finding = _finding(
        severity="CRITICAL",
        category="Authorization",
        confidence="HIGH",
        title="Potential BOLA / IDOR Risk",
    )
    result = engine.score_finding(finding, endpoint)
    assert 0 <= result.risk_score <= 100


def test_risk_level_thresholds() -> None:
    assert score_to_risk_level(95) == "CRITICAL"
    assert score_to_risk_level(90) == "CRITICAL"
    assert score_to_risk_level(82) == "HIGH"
    assert score_to_risk_level(70) == "HIGH"
    assert score_to_risk_level(65) == "MEDIUM"
    assert score_to_risk_level(40) == "MEDIUM"
    assert score_to_risk_level(25) == "LOW"
    assert score_to_risk_level(20) == "LOW"
    assert score_to_risk_level(10) == "INFO"
    assert score_to_risk_level(0) == "INFO"


def test_sensitive_endpoint_increases_score() -> None:
    engine = RiskScoringEngine()
    endpoint = make_endpoint(1, "/users", security_defined=False)
    result = engine.score_finding(_finding(severity="HIGH"), endpoint)
    assert result.risk_factors["endpoint_sensitivity"] == "MEDIUM"
    assert result.risk_score >= 75


def test_state_changing_method_increases_score() -> None:
    engine = RiskScoringEngine()
    get_endpoint = make_endpoint(1, "/items", method="GET", security_defined=True)
    post_endpoint = make_endpoint(2, "/items", method="POST", security_defined=True)
    get_score = engine.score_finding(_finding(severity="MEDIUM", category="Injection"), get_endpoint)
    post_score = engine.score_finding(_finding(severity="MEDIUM", category="Injection"), post_endpoint)
    assert post_score.risk_score > get_score.risk_score


def test_bola_object_identifier_increases_score() -> None:
    engine = RiskScoringEngine()
    endpoint = make_endpoint(1, "/users/{id}")
    result = engine.score_finding(
        _finding(
            severity="MEDIUM",
            category="Authorization",
            title="Potential BOLA / IDOR Risk",
        ),
        endpoint,
    )
    assert result.risk_factors["object_identifier"] is True
    assert result.risk_score >= 60


def test_sensitive_response_data_increases_score_more_than_request() -> None:
    engine = RiskScoringEngine()
    response_endpoint = make_endpoint(
        1,
        "/users",
        responses={
            "200": {
                "description": "OK",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {"password": {"type": "string"}},
                        }
                    }
                },
            }
        },
    )
    request_endpoint = make_endpoint(
        2,
        "/register",
        method="POST",
        request_body={
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"password": {"type": "string"}},
                    }
                }
            }
        },
    )
    response_score = engine.score_finding(
        _finding(
            severity="HIGH",
            category="Sensitive Data",
            evidence="Suspicious field 'password' found in response 200 for GET /users",
        ),
        response_endpoint,
    )
    request_score = engine.score_finding(
        _finding(
            severity="LOW",
            category="Sensitive Data",
            evidence="Suspicious field 'password' found in request body for POST /register",
        ),
        request_endpoint,
    )
    assert response_score.risk_score > request_score.risk_score


def test_missing_authentication_context_increases_score() -> None:
    engine = RiskScoringEngine()
    endpoint = make_endpoint(1, "/users", security_defined=False)
    result = engine.score_finding(_finding(severity="HIGH", category="Authentication"), endpoint)
    assert result.risk_factors["authentication_context"] == "MISSING"
    assert result.risk_score >= 85


def test_confidence_adjustment() -> None:
    engine = RiskScoringEngine()
    endpoint = make_endpoint(1, "/status", security_defined=True)
    high = engine.score_finding(
        _finding(severity="LOW", category="Injection", confidence="HIGH"),
        endpoint,
    )
    low = engine.score_finding(
        _finding(severity="LOW", category="Injection", confidence="LOW"),
        endpoint,
    )
    assert high.risk_score > low.risk_score


def test_scoring_is_deterministic() -> None:
    engine = RiskScoringEngine()
    endpoint = make_endpoint(1, "/users/{id}", security_defined=False)
    finding = _finding(severity="HIGH", category="Authorization", title="Potential BOLA / IDOR Risk")
    first = engine.score_finding(finding, endpoint)
    second = engine.score_finding(finding, endpoint)
    assert first.risk_score == second.risk_score
    assert first.risk_level == second.risk_level
    assert first.risk_factors == second.risk_factors


def test_overall_scan_score_uses_documented_formula() -> None:
    engine = RiskScoringEngine()
    summary = engine.summarize_scan([90, 50, 25])
    assert summary.overall_risk_score == clamp_score(90 + min(int(50 * 0.15) + int(25 * 0.15), 20))
    assert summary.total_findings == 3
    assert summary.critical == 1
    assert summary.medium == 1
    assert summary.low == 1


def test_structured_evidence_contains_endpoint_context() -> None:
    engine = RiskScoringEngine()
    endpoint = make_endpoint(1, "/users/{id}", security_defined=False)
    finding = _finding(severity="HIGH", category="Authorization", title="Potential BOLA / IDOR Risk")
    evidence = engine.build_structured_evidence(finding, endpoint)
    assert evidence["endpoint"] == "GET /users/{id}"
    assert evidence["object_identifier"] == "id"
    assert evidence["security_declared"] is False
