"""Fuse TRIBE-derived perception hypotheses with reviewer-agent feedback."""

from __future__ import annotations

import json
import re
from pathlib import Path


SECTION_ALIASES = {
    "work": "experience",
    "employment": "experience",
    "project": "projects",
    "coursework": "education",
    "technical skills": "skills",
}


def load_json(path: str) -> dict:
    """Load JSON from disk."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_section_name(name: str) -> str:
    """Normalize section names for loose matching."""

    normalized = re.sub(r"[^a-z0-9 ]+", "", str(name).lower()).strip()
    return SECTION_ALIASES.get(normalized, normalized or "unknown")


def _hypotheses_list(perception_hypotheses: dict | list) -> list[dict]:
    if isinstance(perception_hypotheses, list):
        return perception_hypotheses
    return perception_hypotheses.get("hypotheses", [])


def _group_hypotheses_by_section(hypotheses: list[dict]) -> list[dict]:
    grouped: dict[str, list[str]] = {}
    for hypothesis in hypotheses:
        section = normalize_section_name(hypothesis.get("section", "unknown"))
        signal = str(hypothesis.get("hypothesis", "")).strip()
        if signal:
            grouped.setdefault(section, [])
            if signal not in grouped[section]:
                grouped[section].append(signal)
    return [
        {"section": section, "hypothesis": _combine_signals(signals)}
        for section, signals in grouped.items()
    ]


def _combine_signals(signals: list[str]) -> str:
    clauses = []
    for signal in signals:
        for clause in signal.split(";"):
            cleaned = clause.strip()
            if cleaned and cleaned not in clauses:
                clauses.append(cleaned)
    return "; ".join(clauses)


def _perception_source(perception_hypotheses: dict | list) -> str:
    if isinstance(perception_hypotheses, dict):
        metadata = perception_hypotheses.get("metadata", {})
        if metadata.get("mock") or metadata.get("not_real_tribe_output"):
            return "mock"
    return "real_tribe"


def _text_review_confidence(review_summary: dict) -> float | None:
    value = review_summary.get("average_confidence")
    if isinstance(value, int | float):
        return round(float(value), 3)

    reviews = review_summary.get("reviews") or review_summary.get("results") or []
    confidences = [
        float(review["confidence"])
        for review in reviews
        if isinstance(review, dict) and isinstance(review.get("confidence"), int | float)
    ]
    if confidences:
        return round(sum(confidences) / len(confidences), 3)
    return None


def _perception_signal_confidence(source: str) -> float:
    if source == "mock":
        return 0.25
    return 0.50


def _fusion_confidence(source: str, agreement_count: int, target_count: int) -> float:
    perception_confidence = _perception_signal_confidence(source)
    if target_count == 0:
        base = 0.10
    else:
        agreement_ratio = agreement_count / target_count
        base = 0.20 + (0.30 * agreement_ratio)
        if agreement_count >= 2:
            base += 0.05

    if source == "mock":
        base = min(base, 0.30)
    return round(min(base, perception_confidence + 0.20), 3)


def _confidence_breakdown(source: str, review_summary: dict, agreement_count: int, target_count: int) -> dict:
    return {
        "text_review_confidence": _text_review_confidence(review_summary),
        "perception_signal_confidence": _perception_signal_confidence(source),
        "fusion_confidence": _fusion_confidence(source, agreement_count, target_count),
        "explanation": (
            "Text-review confidence comes from reviewer-agent output consistency when available. "
            "Perception-signal confidence reflects how much trust to place in TRIBE-style response features; "
            "mock perception is intentionally capped low because it is not real TRIBE output. "
            "Fusion confidence reflects section-level agreement between reviewer signals and perception hypotheses, "
            "and should not be read as an objective resume-quality score."
        ),
    }


def _review_signals_for_section(review_summary: dict, section: str) -> list[str]:
    section = normalize_section_name(section)
    signals = []
    for key in [
        "recurring_strengths",
        "recurring_concerns",
        "highest_risk_credibility_issue",
        "recommended_next_edit_priority",
    ]:
        value = review_summary.get(key)
        values = value if isinstance(value, list) else [value] if value else []
        for item in values:
            item_text = str(item)
            explicit_section = _explicit_section_for_text(item_text)
            if explicit_section and explicit_section != section:
                continue
            if explicit_section == section or _matches_section_tokens(item_text, section):
                signals.append(item_text)
    return signals


def _section_tokens(section: str) -> list[str]:
    return {
        "experience": ["experience", "internship", "intern", "company", "production", "product", "support", "sem"],
        "projects": ["project", "platform", "tool", "pipeline"],
        "skills": ["skills", "technical skills", "technologies", "tech stack"],
        "education": ["education", "coursework", "gpa", "university"],
    }.get(section, [section])


def _explicit_section_for_text(text: str) -> str | None:
    lowered = text.lower()
    for section in ["education", "experience", "projects", "skills"]:
        if f"{section} section" in lowered or f"({section})" in lowered:
            return section
    if "project" in lowered and ("section" in lowered or "resume insight" in lowered):
        return "projects"
    return None


def _matches_section_tokens(text: str, section: str) -> bool:
    lowered = text.lower()
    for token in _section_tokens(section):
        escaped = re.escape(token.lower())
        if " " in token:
            if escaped.replace("\\ ", " ") in lowered:
                return True
        elif re.search(rf"\b{escaped}\b", lowered):
            return True
    return False


def _evidence_from_resume(resume_text: str, section: str) -> list[str]:
    evidence = []
    for line in resume_text.splitlines():
        if _matches_section_tokens(line, section):
            cleaned = line.strip()
            if cleaned:
                evidence.append(cleaned)
        if len(evidence) >= 3:
            break
    return evidence


def fuse_perception_and_review(
    perception_hypotheses: dict | list,
    review_summary: dict,
    resume_text: str,
) -> dict:
    """Fuse perception hypotheses and reviewer-agent summary into priorities."""

    source = _perception_source(perception_hypotheses)
    caution = (
        "Perception source is mock and not real TRIBE output. Treat all perception signals as development-only proxy hypotheses."
        if source == "mock"
        else "Perception source is treated as real TRIBE-style output, but it still does not prove actual perception or hiring outcomes."
    )
    hypotheses = _group_hypotheses_by_section(_hypotheses_list(perception_hypotheses))

    agreements = []
    disagreements = []
    targets = []

    for hypothesis in hypotheses:
        section = normalize_section_name(hypothesis.get("section", "unknown"))
        perception_signal = hypothesis.get("hypothesis", "")
        reviewer_signals = _review_signals_for_section(review_summary, section)
        reviewer_signal = "; ".join(reviewer_signals[:2]) if reviewer_signals else "No direct reviewer signal found for this section."

        has_density = "dense" in perception_signal or "effortful" in perception_signal
        has_underemphasis = "underemphasized" in perception_signal
        has_reviewer_concern = bool(reviewer_signals)

        if has_reviewer_concern and (has_density or has_underemphasis):
            agreements.append(
                {
                    "section": section,
                    "perception_signal": perception_signal,
                    "reviewer_signal": reviewer_signal,
                    "why_it_matters": "Both signals may suggest this section should be reviewed before patching.",
                }
            )
        elif has_reviewer_concern or has_density or has_underemphasis:
            disagreements.append(
                {
                    "section": section,
                    "perception_signal": perception_signal,
                    "reviewer_signal": reviewer_signal,
                    "interpretation": "Signals do not fully align; treat this as a perception hypothesis to inspect manually.",
                }
            )

        priority_score = 0
        priority_score += 2 if has_reviewer_concern else 0
        priority_score += 1 if has_density else 0
        priority_score += 1 if has_underemphasis else 0
        if priority_score:
            targets.append(
                {
                    "priority_score": priority_score,
                    "section": section,
                    "issue_type": _issue_type(has_density, has_underemphasis, has_reviewer_concern),
                    "evidence": _evidence_from_resume(resume_text, section),
                    "suggested_action": _suggested_action(section, has_density, has_underemphasis),
                    "confidence": "cautious_proxy" if source == "mock" else "experimental_signal",
                    "source_signals": {
                        "perception": perception_signal,
                        "reviewer": reviewer_signal,
                    },
                }
            )

    targets.sort(key=lambda item: item["priority_score"], reverse=True)
    prioritized_targets = []
    for rank, target in enumerate(targets, start=1):
        target = dict(target)
        target["priority_rank"] = rank
        del target["priority_score"]
        prioritized_targets.append(target)

    return {
        "metadata": {
            "perception_source": source,
            "caution": caution,
        },
        "confidence": _confidence_breakdown(source, review_summary, len(agreements), len(prioritized_targets)),
        "agreements": agreements,
        "disagreements": disagreements,
        "prioritized_targets": prioritized_targets,
        "global_summary": _global_summary(source, prioritized_targets),
        "limitations": [
            "This does not predict real hiring outcomes.",
            "This does not claim real brain activity was measured.",
            "TRIBE-style perception features are experimental proxy signals.",
            "Reviewer-agent feedback may still be incomplete or generic.",
        ],
    }


def _issue_type(dense: bool, underemphasized: bool, reviewer: bool) -> str:
    labels = []
    if dense:
        labels.append("density/cognitive-load proxy")
    if underemphasized:
        labels.append("underemphasis proxy")
    if reviewer:
        labels.append("reviewer concern")
    return ", ".join(labels)


def _suggested_action(section: str, dense: bool, underemphasized: bool) -> str:
    if section == "experience":
        return "Patch high-impact bullets to clarify ownership, model/data details, and preserve metrics."
    if section == "projects":
        return "Patch project bullets to surface technical proof and reduce density without deleting evidence."
    if section == "skills":
        return "Group skills for scanability while preserving important technologies."
    if section == "education":
        return "Keep education concise and ensure coursework supports the target role."
    if dense:
        return "Reduce wording density while preserving concrete evidence."
    if underemphasized:
        return "Increase visibility of the strongest evidence in this section."
    return "Inspect section manually before patching."


def _global_summary(source: str, targets: list[dict]) -> str:
    source_text = "mock perception proxy" if source == "mock" else "TRIBE-style perception signal"
    if not targets:
        return f"No high-priority fusion targets found from {source_text} and reviewer summary."
    top = targets[0]["section"]
    return (
        f"The strongest fused improvement target is `{top}` based on {source_text} "
        "plus reviewer-agent feedback. Treat this as a cautious prioritization hypothesis."
    )
