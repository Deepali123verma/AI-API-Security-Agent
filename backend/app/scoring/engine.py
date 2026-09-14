from app.models.endpoint import Endpoint
from app.scanner.models import ScannerFinding
from app.scanner.helpers import has_object_identifier
from app.scoring.helpers import (
    build_structured_evidence,
    detect_sensitive_data_context,
    endpoint_sensitivity,
    extract_object_identifier,
)
from app.scoring.models import ScanRiskSummary, ScoreResult
from app.scoring.rules import (
    ADDITIONAL_FINDING_MAX_EACH,
    ADDITIONAL_FINDING_TOTAL_CAP,
    ADDITIONAL_FINDING_WEIGHT,
    AUTHENTICATION_CATEGORIES,
    AUTHORIZATION_CATEGORIES,
    BASE_SEVERITY_SCORES,
    CONFIDENCE_ADJUSTMENTS,
    SENSITIVE_DATA_CATEGORIES,
    STATE_CHANGING_METHODS,
    clamp_score,
    score_to_risk_level,
)


class RiskScoringEngine:
    """Deterministic scoring engine. Same input always produces the same output."""

    def score_finding(
        self,
        finding: ScannerFinding,
        endpoint: Endpoint | None,
    ) -> ScoreResult:
        base_severity = finding.severity.upper()
        score = BASE_SEVERITY_SCORES.get(base_severity, BASE_SEVERITY_SCORES["MEDIUM"])
        factors: dict[str, object] = {
            "base_severity": base_severity,
            "endpoint_sensitivity": "NORMAL",
            "method": endpoint.method if endpoint else None,
            "path": endpoint.path if endpoint else None,
            "object_identifier": False,
            "sensitive_data": False,
            "sensitive_response_data": False,
            "sensitive_request_data": False,
            "authentication_context": None,
            "confidence": finding.confidence.upper(),
        }

        if endpoint is not None:
            sensitivity = endpoint_sensitivity(endpoint.path)
            factors["endpoint_sensitivity"] = sensitivity
            if sensitivity == "HIGH":
                score += 10
            elif sensitivity == "MEDIUM":
                score += 5

            if endpoint.method in STATE_CHANGING_METHODS:
                score += 5
                factors["state_changing_method"] = True
            else:
                factors["state_changing_method"] = False

        if (
            finding.category in AUTHORIZATION_CATEGORIES
            and endpoint is not None
            and has_object_identifier(endpoint)
        ):
            score += 10
            factors["object_identifier"] = True
            identifier = extract_object_identifier(endpoint.path)
            if identifier:
                factors["object_identifier_name"] = identifier

        response_sensitive, request_sensitive = detect_sensitive_data_context(finding, endpoint)
        if finding.category in SENSITIVE_DATA_CATEGORIES:
            if response_sensitive:
                score += 15
                factors["sensitive_data"] = True
                factors["sensitive_response_data"] = True
            elif request_sensitive:
                score += 5
                factors["sensitive_data"] = True
                factors["sensitive_request_data"] = True

        if (
            finding.category in AUTHENTICATION_CATEGORIES
            and endpoint is not None
            and not endpoint.security_defined
        ):
            score += 10
            factors["authentication_context"] = "MISSING"
        elif endpoint is not None and endpoint.security_defined:
            factors["authentication_context"] = "DOCUMENTED"

        confidence = finding.confidence.upper()
        score += CONFIDENCE_ADJUSTMENTS.get(confidence, 0)
        factors["confidence_adjustment"] = CONFIDENCE_ADJUSTMENTS.get(confidence, 0)

        final_score = clamp_score(score)
        risk_level = score_to_risk_level(final_score)
        factors["final_score"] = final_score
        factors["risk_level"] = risk_level

        return ScoreResult(
            risk_score=final_score,
            risk_level=risk_level,
            risk_factors=factors,
        )

    def build_structured_evidence(
        self,
        finding: ScannerFinding,
        endpoint: Endpoint | None,
    ) -> dict:
        return build_structured_evidence(finding, endpoint)

    def summarize_scan(self, finding_scores: list[int]) -> ScanRiskSummary:
        """Overall score = highest finding score + capped contribution from others.

        Each additional finding contributes min(score * 0.15, 8) points.
        Total additional contribution is capped at 20 points.
        """
        if not finding_scores:
            return ScanRiskSummary(
                total_findings=0,
                critical=0,
                high=0,
                medium=0,
                low=0,
                info=0,
                overall_risk_score=0,
                risk_level="INFO",
            )

        risk_levels = [score_to_risk_level(score) for score in finding_scores]
        sorted_scores = sorted(finding_scores, reverse=True)
        highest = sorted_scores[0]

        additional = 0
        for score in sorted_scores[1:]:
            additional += min(int(score * ADDITIONAL_FINDING_WEIGHT), ADDITIONAL_FINDING_MAX_EACH)
        overall = clamp_score(highest + min(additional, ADDITIONAL_FINDING_TOTAL_CAP))

        return ScanRiskSummary(
            total_findings=len(finding_scores),
            critical=risk_levels.count("CRITICAL"),
            high=risk_levels.count("HIGH"),
            medium=risk_levels.count("MEDIUM"),
            low=risk_levels.count("LOW"),
            info=risk_levels.count("INFO"),
            overall_risk_score=overall,
            risk_level=score_to_risk_level(overall),
        )
