"""Deterministic perception insights from section proxy rankings."""

from __future__ import annotations


def build_proxy_rankings(section_signals: list[dict]) -> dict:
    """Rank section signals by the core proxy values."""

    return {
        "salience_proxy": _rank(section_signals, "salience_proxy"),
        "position_normalized_salience": _rank(
            [
                item
                for item in section_signals
                if item.get("position_normalized_salience") is not None
            ],
            "position_normalized_salience",
        ),
        "cognitive_load_proxy": _rank(section_signals, "cognitive_load_proxy"),
        "underemphasis_proxy": _rank(section_signals, "underemphasis_proxy"),
    }


def generate_deterministic_insights(section_signals: list[dict]) -> list[dict]:
    """Generate ranking-driven insights that do not depend on LLM wording."""

    rankings = build_proxy_rankings(section_signals)
    insights = []
    for signal_type, ranked in rankings.items():
        if not ranked:
            continue
        top = ranked[0]
        insights.append(
            {
                "section": top["section"],
                "signal_type": signal_type,
                "value": top["value"],
                "rank": top["rank"],
                "evidence_phrases": top.get("evidence_phrases", []),
                "interpretation": _interpretation(signal_type, top),
                "suggestion": _suggestion(signal_type, top),
                "caution": (
                    "This is a deterministic proxy insight from section rankings, "
                    "not a measured reader response or hiring prediction."
                ),
            }
        )
    raw = rankings.get("salience_proxy", [])
    normalized = rankings.get("position_normalized_salience", [])
    if raw and normalized and raw[0]["section"] != normalized[0]["section"]:
        raw_section = raw[0]["section"]
        normalized_section = normalized[0]["section"]
        if raw_section.lower() in {"intro", "education", "education / coursework"}:
            insights.append(
                {
                    "section": normalized_section,
                    "signal_type": "raw_vs_position_normalized_salience_shift",
                    "value": normalized[0]["value"],
                    "rank": 1,
                    "evidence_phrases": normalized[0].get("evidence_phrases", []),
                    "interpretation": (
                        f"Raw salience is highest early in {raw_section}, but "
                        f"position-normalized salience shifts attention to {normalized_section}."
                    ),
                    "suggestion": (
                        f"Inspect {normalized_section} as a possible substantive signal after "
                        "accounting for early-section position effects."
                    ),
                    "caution": (
                        "Position-normalized salience is a transparent heuristic, not a "
                        "TRIBE-native neuroscience metric."
                    ),
                }
            )
    return insights


def _rank(section_signals: list[dict], key: str) -> list[dict]:
    ranked = sorted(
        section_signals,
        key=lambda item: _numeric(item.get(key)),
        reverse=True,
    )
    return [
        {
            **item,
            "rank": index,
            "value": round(_numeric(item.get(key)), 4),
        }
        for index, item in enumerate(ranked, start=1)
    ]


def _interpretation(signal_type: str, item: dict) -> str:
    section = item.get("section", "This section")
    value = _numeric(item.get(signal_type))
    if signal_type == "salience_proxy":
        return (
            f"{section} has the highest salience_proxy ({value:.4f}), which may "
            "suggest it dominates the first-pass predicted response pattern."
        )
    if signal_type == "cognitive_load_proxy":
        return (
            f"{section} has the highest cognitive_load_proxy ({value:.4f}), which "
            "may suggest this section is denser or more effortful to scan."
        )
    if signal_type == "position_normalized_salience":
        return (
            f"{section} has the highest position_normalized_salience ({value:.4f}), "
            "which may suggest it remains salient after reducing early-position dominance."
        )
    return (
        f"{section} has the highest underemphasis_proxy ({value:.4f}), which may "
        "suggest important evidence is less prominent than other sections."
    )


def _suggestion(signal_type: str, item: dict) -> str:
    section = item.get("section", "this section")
    evidence = item.get("evidence_phrases", [])
    evidence_clause = f" Evidence to inspect: {evidence[0]}." if evidence else ""
    if signal_type == "salience_proxy":
        return (
            f"Because {section} has the highest salience_proxy, inspect whether "
            f"this section dominates the first-pass signal more than intended.{evidence_clause}"
        )
    if signal_type == "cognitive_load_proxy":
        return (
            f"Because {section} has the highest cognitive_load_proxy, inspect "
            "whether the section is dense, long, or combines too many metrics or "
            f"technologies in one span.{evidence_clause}"
        )
    if signal_type == "position_normalized_salience":
        return (
            f"Because {section} has the highest position_normalized_salience, inspect "
            "whether this section carries a strong signal beyond early document position."
            f"{evidence_clause}"
        )
    return (
        f"Because {section} has the highest underemphasis_proxy, inspect whether "
        f"important evidence is buried or should be surfaced more clearly.{evidence_clause}"
    )


def _numeric(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
