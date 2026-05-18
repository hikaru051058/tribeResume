"""Rule-based quality checks for Ollama reviewer JSON outputs."""

from __future__ import annotations

import json
from pathlib import Path


REQUIRED_FIELDS = {
    "persona",
    "rating",
    "confidence",
    "first_impression",
    "strongest_signals",
    "weak_or_confusing_signals",
    "credibility_risks",
    "evidence_quotes",
    "suggested_fixes",
    "final_summary",
}

VALID_RATINGS = {"Great", "Good", "Mixed", "Weak", "Bad"}

GENERIC_PHRASES = [
    "tailor your resume",
    "add more metrics",
    "improve clarity",
]


def load_review_output(path: str) -> dict:
    """Load review JSON output from disk."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def _iter_reviews(payload: dict) -> list[dict]:
    if isinstance(payload.get("reviews"), list):
        return payload["reviews"]
    if isinstance(payload, list):
        return payload
    return [payload]


def check_required_fields(review: dict) -> list[str]:
    """Check whether a single review contains all required fields."""

    missing = sorted(REQUIRED_FIELDS - set(review))
    return [f"Missing required field: {field}" for field in missing]


def check_evidence_quotes_present(review: dict) -> list[str]:
    """Check whether evidence quotes exist and contain quote/reason."""

    issues = []
    evidence_quotes = review.get("evidence_quotes")
    if not isinstance(evidence_quotes, list) or not evidence_quotes:
        return ["Missing evidence_quotes or evidence_quotes is empty."]
    for index, item in enumerate(evidence_quotes):
        if not isinstance(item, dict):
            issues.append(f"Evidence quote {index} is not an object.")
            continue
        if not item.get("quote"):
            issues.append(f"Evidence quote {index} is missing quote text.")
        if not item.get("reason"):
            issues.append(f"Evidence quote {index} is missing reason.")
    return issues


def check_confidence_range(review: dict) -> list[str]:
    """Check whether confidence is numeric and between 0 and 1."""

    confidence = review.get("confidence")
    if not isinstance(confidence, int | float):
        return ["Confidence is not numeric."]
    if confidence < 0 or confidence > 1:
        return ["Confidence is outside 0..1."]
    return []


def check_rating_valid(review: dict) -> list[str]:
    """Check whether rating is one of the allowed response labels."""

    rating = review.get("rating")
    if rating not in VALID_RATINGS:
        return [f"Invalid rating: {rating!r}."]
    return []


def check_generic_feedback(review: dict) -> list[str]:
    """Flag generic advice that appears without enough evidence support."""

    issues = []
    evidence_quotes = review.get("evidence_quotes")
    has_evidence = isinstance(evidence_quotes, list) and bool(evidence_quotes)
    searchable_parts = []
    for key in [
        "first_impression",
        "strongest_signals",
        "weak_or_confusing_signals",
        "credibility_risks",
        "suggested_fixes",
        "final_summary",
    ]:
        value = review.get(key)
        if isinstance(value, list):
            searchable_parts.extend(str(item) for item in value)
        elif value is not None:
            searchable_parts.append(str(value))

    combined = " ".join(searchable_parts).lower()
    for phrase in GENERIC_PHRASES:
        if phrase in combined and not has_evidence:
            issues.append(f"Generic feedback without evidence quotes: {phrase}")
        elif phrase in combined and len(str(evidence_quotes)) < 80:
            issues.append(f"Generic feedback with weak evidence support: {phrase}")
    return issues


def evaluate_review_file(path: str) -> dict:
    """Evaluate all reviews in a review output file."""

    payload = load_review_output(path)
    reviews = _iter_reviews(payload)
    review_results = []
    issue_count = 0

    for index, review in enumerate(reviews):
        issues = []
        if not isinstance(review, dict):
            issues = [f"Review {index} is not an object."]
        else:
            issues.extend(check_required_fields(review))
            issues.extend(check_evidence_quotes_present(review))
            issues.extend(check_confidence_range(review))
            issues.extend(check_rating_valid(review))
            issues.extend(check_generic_feedback(review))
        issue_count += len(issues)
        review_results.append(
            {
                "index": index,
                "persona": review.get("persona") if isinstance(review, dict) else None,
                "rating": review.get("rating") if isinstance(review, dict) else None,
                "issue_count": len(issues),
                "issues": issues,
            }
        )

    return {
        "path": path,
        "review_count": len(reviews),
        "issue_count": issue_count,
        "passed": issue_count == 0,
        "reviews": review_results,
    }

