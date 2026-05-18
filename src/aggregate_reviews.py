"""Aggregate local reviewer-agent results."""

from __future__ import annotations

from collections import Counter


RATING_TO_SCORE = {
    "Great": 5,
    "Good": 4,
    "Mixed": 3,
    "Weak": 2,
    "Bad": 1,
}

SCORE_TO_RATING = {
    5: "Great",
    4: "Good",
    3: "Mixed",
    2: "Weak",
    1: "Bad",
}


def _most_common_text(items: list[str], limit: int = 5) -> list[str]:
    normalized = [item.strip() for item in items if item and item.strip()]
    counts = Counter(normalized)
    return [item for item, _ in counts.most_common(limit)]


def aggregate_review_results(results: list[dict]) -> dict:
    """Aggregate persona review outputs into a compact summary."""

    valid_results = [
        result for result in results if result.get("rating") in RATING_TO_SCORE
    ]
    if not valid_results:
        return {
            "rating_distribution": {},
            "average_confidence": 0.0,
            "final_overall_rating": "Mixed",
            "recurring_strengths": [],
            "recurring_concerns": ["No valid reviewer results were available."],
            "highest_risk_credibility_issue": "No valid credibility assessment available.",
            "recommended_next_edit_priority": "Run reviewer agents successfully before editing.",
        }

    rating_distribution = Counter(result["rating"] for result in valid_results)
    average_score = sum(RATING_TO_SCORE[result["rating"]] for result in valid_results)
    average_score /= len(valid_results)
    rounded_score = min(5, max(1, round(average_score)))

    confidence_values = [
        float(result.get("confidence", 0))
        for result in valid_results
        if isinstance(result.get("confidence"), int | float)
    ]
    average_confidence = (
        sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
    )

    strengths = []
    concerns = []
    risks = []
    fixes = []
    for result in valid_results:
        strengths.extend(result.get("strongest_signals", []))
        concerns.extend(result.get("weak_or_confusing_signals", []))
        risks.extend(result.get("credibility_risks", []))
        fixes.extend(result.get("suggested_fixes", []))

    recurring_concerns = _most_common_text(concerns)
    highest_risk = _most_common_text(risks, limit=1)
    edit_priority = _most_common_text(fixes, limit=1)

    return {
        "rating_distribution": dict(rating_distribution),
        "average_confidence": round(average_confidence, 3),
        "final_overall_rating": SCORE_TO_RATING[rounded_score],
        "recurring_strengths": _most_common_text(strengths),
        "recurring_concerns": recurring_concerns,
        "highest_risk_credibility_issue": (
            highest_risk[0] if highest_risk else "No major credibility issue repeated."
        ),
        "recommended_next_edit_priority": (
            edit_priority[0]
            if edit_priority
            else "Add clearer evidence for the most important role-fit claims."
        ),
    }

