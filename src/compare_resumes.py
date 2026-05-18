"""Rule-based before/after resume comparison."""

from __future__ import annotations

import re
from collections import Counter

from evidence_extractor import extract_resume_evidence


RATING_TO_SCORE = {
    "Great": 5,
    "Good": 4,
    "Mixed": 3,
    "Weak": 2,
    "Bad": 1,
}


ACTION_VERBS = {
    "built",
    "created",
    "implemented",
    "improved",
    "reduced",
    "added",
    "optimized",
    "designed",
    "maintained",
    "supported",
    "collaborated",
    "developed",
}


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9+#./'_-]*", text.lower())


def _bullets(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip().startswith("-")]


def _metric_count(text: str) -> int:
    return len(re.findall(r"\b\d+(\.\d+)?\s*[%xkKmM]?\b", text))


def _section_count(text: str) -> int:
    section_names = {"education", "experience", "projects", "skills"}
    lines = [line.strip().lower() for line in text.splitlines()]
    return sum(1 for line in lines if line in section_names)


def _action_verb_count(text: str) -> int:
    counts = Counter(_words(text))
    return sum(counts[verb] for verb in ACTION_VERBS)


def _summary_score(summary: dict | None) -> int | None:
    if not summary:
        return None
    rating = summary.get("final_overall_rating")
    return RATING_TO_SCORE.get(rating)


def _trend_label(delta: float, positive: str, neutral: str, negative: str) -> str:
    if delta > 0.05:
        return positive
    if delta < -0.05:
        return negative
    return neutral


def compare_resume_texts(
    original_text: str,
    revised_text: str,
    original_summary: dict | None = None,
    revised_summary: dict | None = None,
) -> dict:
    """Compare original and revised resumes using simple deterministic signals."""

    original_words = _words(original_text)
    revised_words = _words(revised_text)
    original_bullets = _bullets(original_text)
    revised_bullets = _bullets(revised_text)

    original_avg_bullet = (
        sum(len(_words(bullet)) for bullet in original_bullets) / len(original_bullets)
        if original_bullets
        else 0
    )
    revised_avg_bullet = (
        sum(len(_words(bullet)) for bullet in revised_bullets) / len(revised_bullets)
        if revised_bullets
        else 0
    )

    clarity_delta = 0.0
    if original_avg_bullet:
        clarity_delta += (original_avg_bullet - revised_avg_bullet) / max(
            original_avg_bullet, 1
        )
    clarity_delta += min(_section_count(revised_text) - _section_count(original_text), 1) * 0.1

    credibility_delta = 0.0
    credibility_delta += min(_metric_count(revised_text) - _metric_count(original_text), 2) * 0.1
    credibility_delta += min(
        _action_verb_count(revised_text) - _action_verb_count(original_text), 3
    ) * 0.05

    ats_delta = 0.0
    ats_delta += min(_section_count(revised_text) - _section_count(original_text), 1) * 0.15
    if len(revised_words) <= len(original_words) * 1.15:
        ats_delta += 0.05
    else:
        ats_delta -= 0.1

    original_score = _summary_score(original_summary)
    revised_score = _summary_score(revised_summary)
    rating_delta = (
        revised_score - original_score
        if original_score is not None and revised_score is not None
        else None
    )

    original_evidence = extract_resume_evidence(original_text)
    revised_evidence = extract_resume_evidence(revised_text)
    revised_evidence_lower = "\n".join(revised_evidence["all"]).lower()
    original_evidence_lower = "\n".join(original_evidence["all"]).lower()
    missing_evidence = [
        item for item in original_evidence["all"] if item.lower() not in revised_evidence_lower
    ]
    added_evidence = [
        item for item in revised_evidence["all"] if item.lower() not in original_evidence_lower
    ]
    evidence_preservation_score = (
        1 - (len(missing_evidence) / max(len(original_evidence["all"]), 1))
        if original_evidence["all"]
        else 1.0
    )

    if evidence_preservation_score < 0.85:
        credibility_delta -= 0.3

    remaining_risks = []
    if evidence_preservation_score < 0.85:
        remaining_risks.append(
            "The revised resume appears to remove concrete evidence from the original."
        )
    if _metric_count(revised_text) == 0:
        remaining_risks.append("The revised resume still has no quantified outcomes.")
    if revised_avg_bullet > 24:
        remaining_risks.append("Some revised bullets may still be too long.")
    if "ai" in revised_text.lower() and "model" not in revised_text.lower():
        remaining_risks.append("AI-related wording may still need more technical evidence.")
    if not remaining_risks:
        remaining_risks.append("No obvious rule-based risk detected; human review is still needed.")

    if rating_delta is not None and rating_delta > 0:
        response_change = "Reviewer-agent summary improved after the rewrite."
    elif rating_delta is not None and rating_delta < 0:
        response_change = "Reviewer-agent summary declined after the rewrite."
    else:
        response_change = _trend_label(
            clarity_delta + credibility_delta + ats_delta,
            "Likely modestly stronger reader response based on rule-based signals.",
            "Likely similar reader response; changes may be incremental.",
            "Potentially weaker reader response; review the rewrite before using it.",
        )

    return {
        "clarity_improvement": _trend_label(
            clarity_delta,
            "Improved: bullets or structure appear easier to scan.",
            "Mostly unchanged: readability signals are similar.",
            "Worse: revised text may be denser or less scannable.",
        ),
        "credibility_improvement": (
            "Worse: revised text removed concrete evidence from the original."
            if evidence_preservation_score < 0.85
            else _trend_label(
                credibility_delta,
                "Improved: revised text uses stronger action/evidence signals.",
                "Mostly unchanged: evidence strength looks similar.",
                "Worse: revised text may have weaker concrete evidence.",
            )
        ),
        "ats_improvement": _trend_label(
            ats_delta,
            "Improved: structure and length look ATS-friendlier.",
            "Mostly unchanged: ATS-readable structure appears similar.",
            "Worse: revised text may be less ATS-friendly.",
        ),
        "remaining_risks": remaining_risks,
        "likely_reader_response_change": response_change,
        "final_recommendation": (
            "Do not use the revised version without restoring missing concrete evidence."
            if evidence_preservation_score < 0.85
            else (
                "Use the revised resume as a draft, then verify every claim before sending."
                if "declined" not in response_change and "weaker" not in response_change
                else "Do not use the revised version without manual edits."
            )
        ),
        "metrics": {
            "original_word_count": len(original_words),
            "revised_word_count": len(revised_words),
            "original_bullet_count": len(original_bullets),
            "revised_bullet_count": len(revised_bullets),
            "original_avg_bullet_words": round(original_avg_bullet, 2),
            "revised_avg_bullet_words": round(revised_avg_bullet, 2),
            "original_metric_count": _metric_count(original_text),
            "revised_metric_count": _metric_count(revised_text),
            "rating_delta": rating_delta,
            "original_evidence_count": len(original_evidence["all"]),
            "revised_evidence_count": len(revised_evidence["all"]),
            "missing_evidence": missing_evidence,
            "added_evidence": added_evidence,
            "evidence_preservation_score": round(evidence_preservation_score, 3),
        },
    }
