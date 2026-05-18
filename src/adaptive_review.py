"""Adaptive reviewer escalation rules."""

from __future__ import annotations

from evaluate_outputs import (
    check_evidence_quotes_present,
    check_generic_feedback,
)


ESCALATION_RATINGS = {"Mixed", "Weak", "Bad"}


def _target_role_contains(target_role: str | None, keywords: list[str]) -> list[str]:
    if not target_role:
        return []
    lowered = target_role.lower()
    return [keyword for keyword in keywords if keyword.lower() in lowered]


def should_escalate_review(
    review: dict,
    persona: str,
    target_role: str | None,
    adaptive_config: dict,
) -> tuple[bool, list[str]]:
    """Decide whether one fast-pass review should be escalated."""

    reasons = []

    if persona in adaptive_config.get("always_escalate", []):
        reasons.append("persona is always escalated")

    rating = review.get("rating")
    if rating in ESCALATION_RATINGS:
        reasons.append(f"rating is {rating}")

    confidence = review.get("confidence")
    if not isinstance(confidence, int | float):
        reasons.append("confidence is missing or non-numeric")
    elif confidence < 0.70:
        reasons.append(f"confidence below 0.70 ({confidence:.2f})")

    evidence_issues = check_evidence_quotes_present(review)
    if evidence_issues:
        reasons.append("missing or weak evidence quotes")

    generic_issues = check_generic_feedback(review)
    if generic_issues:
        reasons.append("generic feedback detected")

    role_rules = adaptive_config.get("role_based_escalate", {})
    role_keywords = role_rules.get(persona, [])
    matched_keywords = _target_role_contains(target_role, role_keywords)
    if matched_keywords:
        reasons.append(
            "target role matched escalation keyword(s): "
            + ", ".join(matched_keywords)
        )

    return bool(reasons), reasons


def merge_adaptive_reviews(
    first_pass_results: list[dict], escalated_results: list[dict]
) -> list[dict]:
    """Replace first-pass reviews with successful escalated reviews by persona."""

    escalated_by_persona = {
        review.get("persona"): review for review in escalated_results if review.get("persona")
    }
    merged = []
    for first_pass in first_pass_results:
        persona = first_pass.get("persona")
        escalated = escalated_by_persona.get(persona)
        if escalated and not escalated.get("error"):
            merged.append(escalated)
        elif escalated and escalated.get("error"):
            kept = dict(first_pass)
            kept["escalation_error"] = escalated["error"]
            kept["escalated_model"] = escalated.get("model")
            kept["escalation_reasons"] = escalated.get("escalation_reasons", [])
            merged.append(kept)
        else:
            merged.append(first_pass)
    return merged

