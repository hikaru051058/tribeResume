"""Markdown formatter for document perception interpretation reports."""

from __future__ import annotations

from explain_tribe_outputs import (
    explain_cognitive_load_proxy,
    explain_mock_vs_real_source,
    explain_response_intensity,
    explain_section_salience,
    explain_underemphasis_proxy,
)


def format_perception_report(result: dict, reviewer_comparison: dict | None = None) -> str:
    """Format perception interpretation JSON as a Markdown report."""

    metadata = result.get("metadata", {})
    perception_source = metadata.get("perception_source", "unknown")
    explanation = result.get("tribe_output_explanation", {})

    lines = [
        "# Document Perception Report",
        "",
        _mode_banner(perception_source),
        "",
        "## Important Caution",
        "",
        f"- Perception source: `{perception_source}`",
        f"- {_source_caution(perception_source)}",
        "- No actual brain scan was performed.",
        "- This does not predict hiring outcomes.",
        "- Suggestions are inspection priorities, not automatic edits.",
        "",
        "## What TRIBE Output Represents",
        "",
        f"- Response intensity: {explanation.get('what_raw_output_means') or explain_response_intensity()}",
        f"- Salience: {explain_section_salience()}",
        "- Position-normalized salience: A transparent heuristic that tries to reduce early-section dominance in synthetic reading events. It is not a TRIBE-native neuroscience metric.",
        f"- Cognitive-load proxy: {explain_cognitive_load_proxy()}",
        f"- Underemphasis proxy: {explain_underemphasis_proxy()}",
        f"- Section-level hypotheses: {explanation.get('what_features_mean', '')}",
        f"- What cannot be concluded: {explanation.get('what_cannot_be_concluded', '')}",
        "",
        "## Overall Perception Summary",
        "",
        result.get("overall_perception_summary", ""),
        "",
    ]
    if perception_source == "real_tribe":
        lines.extend(
            _raw_tribe_signal_summary(result.get("raw_tribe_signal_summary", {}))
        )
    section_signals = result.get("section_level_signals", [])
    lines.extend(["## Proxy Signal Rankings", ""])
    lines.extend(_ranking_table("Highest Salience", section_signals, "salience_proxy"))
    if any(item.get("position_normalized_salience") is not None for item in section_signals):
        lines.extend(
            _ranking_table(
                "Highest Position-Normalized Salience",
                section_signals,
                "position_normalized_salience",
            )
        )
    lines.extend(_ranking_table("Highest Cognitive Load Proxy", section_signals, "cognitive_load_proxy"))
    lines.extend(_ranking_table("Most Underemphasized", section_signals, "underemphasis_proxy"))
    lines.extend(_deterministic_insights(result.get("deterministic_insights", [])))
    lines.extend(["## Section-Level Signals", ""])

    for item in section_signals:
        lines.extend(
            [
                f"### {item.get('section', 'unknown')}",
                "",
                "Proxy signals:",
                f"- salience_proxy: {_format_proxy(item.get('salience_proxy'))}",
                f"- position_normalized_salience: {_format_proxy(item.get('position_normalized_salience'))}",
                f"- cognitive_load_proxy: {_format_proxy(item.get('cognitive_load_proxy'))}",
                f"- underemphasis_proxy: {_format_proxy(item.get('underemphasis_proxy'))}",
                f"- response_intensity: {_format_proxy(item.get('response_intensity'))}",
                f"- source: {perception_source}",
                "",
                "Resume evidence:",
            ]
        )
        evidence = item.get("evidence_phrases", [])
        lines.extend([f"- {quote}" for quote in evidence] or ["- None extracted"])
        lines.extend(
            [
                "",
                "Interpretation:",
                f"- Possible meaning: {item.get('possible_meaning', '')}",
                f"- Why it matters: {item.get('reader_effect_hypothesis', '')}",
                f"- Cautious caveat: {item.get('caution', '')}",
                "",
                "Suggestion:",
                f"- {item.get('suggestion', '')}",
                "",
            ]
        )
    if not result.get("section_level_signals"):
        lines.extend(["No section-level signals were listed.", ""])

    lines.extend(["## Suggestion Priorities", ""])
    for item in result.get("suggestion_priorities", []):
        lines.extend(
            [
                f"### Priority {item.get('priority', '')}: {item.get('section', 'unknown')}",
                f"- Suggestion: {item.get('suggestion', '')}",
                f"- Why: {item.get('why', '')}",
                f"- Reasoning: {item.get('reasoning', '')}",
                "- Source signals:",
                f"  - salience_proxy: {_format_proxy(item.get('source_signals', {}).get('salience_proxy'))}",
                f"  - cognitive_load_proxy: {_format_proxy(item.get('source_signals', {}).get('cognitive_load_proxy'))}",
                f"  - underemphasis_proxy: {_format_proxy(item.get('source_signals', {}).get('underemphasis_proxy'))}",
                "- Evidence used:",
            ]
        )
        evidence = item.get("source_signals", {}).get("evidence_phrases", [])
        lines.extend([f"  - {quote}" for quote in evidence] or ["  - None listed"])
        lines.append("")
    if not result.get("suggestion_priorities"):
        lines.extend(["No suggestion priorities were listed.", ""])

    lines.extend(["## Optional Reviewer Comparison", ""])
    if reviewer_comparison:
        lines.extend(
            [
                f"- Review source: {reviewer_comparison.get('source', 'provided')}",
                f"- Summary: {reviewer_comparison.get('summary', '')}",
                "",
            ]
        )
    else:
        lines.extend(["No reviewer-agent comparison was included in this report.", ""])

    lines.extend(["## Limitations", ""])
    for item in result.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _format_proxy(value: object) -> str:
    if isinstance(value, int | float):
        return f"{float(value):.4f}"
    if value is None:
        return "not available"
    return str(value)


def _raw_tribe_signal_summary(summary: dict) -> list[str]:
    return [
        "## Raw TRIBE Signal Summary",
        "",
        f"- prediction shape: `{summary.get('prediction_shape', 'not available')}`",
        f"- retained segments: `{summary.get('retained_segments', 'not available')}`",
        f"- output dimensions: `{summary.get('output_dimensions', 'not available')}`",
        f"- synthetic event warning: {summary.get('synthetic_event_warning', 'Synthetic resume-reading events were used.')}",
        f"- timeline analysis: `{summary.get('timeline_analysis_path') or 'not provided'}`",
        "",
    ]


def _deterministic_insights(insights: list[dict]) -> list[str]:
    lines = ["## Deterministic Signal Insights", ""]
    if not insights:
        return lines + ["No deterministic signal insights were generated.", ""]
    for insight in insights:
        lines.extend(
            [
                f"### {insight.get('section', 'unknown')} - {insight.get('signal_type', 'signal')}",
                f"- Rank: {insight.get('rank', '')}",
                f"- Value: {_format_proxy(insight.get('value'))}",
                f"- Interpretation: {insight.get('interpretation', '')}",
                f"- Suggestion: {insight.get('suggestion', '')}",
                f"- Caution: {insight.get('caution', '')}",
                "- Evidence:",
            ]
        )
        evidence = insight.get("evidence_phrases", [])
        lines.extend([f"  - {item}" for item in evidence[:5]] or ["  - None extracted"])
        lines.append("")
    return lines


def _source_caution(perception_source: str) -> str:
    if perception_source == "real_tribe":
        return (
            "This uses real TRIBE v2 checkpoint output, but from synthetic "
            "resume-reading events. No human was scanned."
        )
    return explain_mock_vs_real_source(perception_source)


def _mode_banner(perception_source: str) -> str:
    if perception_source == "mock":
        return (
            "**DEMO MODE:** This report uses mock proxy values. It is only for "
            "testing the report pipeline and should not be used to interpret "
            "the document."
        )
    if perception_source == "real_tribe":
        return (
            "**EXPERIMENTAL REAL TRIBE MODE:** This report uses real TRIBE v2 "
            "checkpoint output from synthetic resume-reading events. No human "
            "was scanned."
        )
    return (
        "**UNKNOWN PERCEPTION SOURCE:** Treat this report as experimental until "
        "the source is verified."
    )


def _ranking_table(title: str, section_signals: list[dict], key: str) -> list[str]:
    lines = [
        f"### {title}",
        "",
        "| Rank | Section | Value | Short Interpretation |",
        "| --- | --- | ---: | --- |",
    ]
    ranked = sorted(
        section_signals,
        key=lambda item: _numeric_value(item.get(key)),
        reverse=True,
    )
    for index, item in enumerate(ranked, start=1):
        lines.append(
            f"| {index} | {item.get('section', 'unknown')} | "
            f"{_format_proxy(item.get(key))} | {_ranking_interpretation(key, item)} |"
        )
    lines.append("")
    return lines


def _numeric_value(value: object) -> float:
    return float(value) if isinstance(value, int | float) else 0.0


def _ranking_interpretation(key: str, item: dict) -> str:
    section = item.get("section", "section")
    if key == "salience_proxy":
        return f"{section} may be more likely to stand out as a proxy signal."
    if key == "cognitive_load_proxy":
        return f"{section} may be more effortful or dense to scan."
    if key == "underemphasis_proxy":
        return f"{section} may be less prominent relative to other sections."
    if key == "position_normalized_salience":
        return f"{section} remains salient after a simple position-bias adjustment."
    return item.get("possible_meaning", "")
