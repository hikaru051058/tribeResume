"""Markdown formatter for perception-review fusion reports."""

from __future__ import annotations


def format_fusion_report(report: dict) -> str:
    """Format fusion report JSON as Markdown."""

    metadata = report.get("metadata", {})
    lines = [
        "# Perception + Review Fusion Report",
        "",
        "## Important Caution",
        "",
        f"Perception source: `{metadata.get('perception_source', 'unknown')}`",
        "",
        metadata.get("caution", ""),
        "",
        "## Confidence Breakdown",
        "",
    ]
    confidence = report.get("confidence", {})
    lines.extend(
        [
            f"- Text-review confidence: {_format_confidence(confidence.get('text_review_confidence'))}",
            f"- Perception-signal confidence: {_format_confidence(confidence.get('perception_signal_confidence'))}",
            f"- Fusion confidence: {_format_confidence(confidence.get('fusion_confidence'))}",
            f"- Explanation: {confidence.get('explanation', '')}",
            "",
        ]
    )

    lines.extend(
        [
        "## Global Summary",
        "",
        report.get("global_summary", ""),
        "",
        "## Agreements",
        "",
        ]
    )
    for item in report.get("agreements", []):
        lines.extend(
            [
                f"### {item.get('section', 'unknown')}",
                f"- Perception signal: {item.get('perception_signal', '')}",
                f"- Reviewer signal: {item.get('reviewer_signal', '')}",
                f"- Why it matters: {item.get('why_it_matters', '')}",
                "",
            ]
        )
    if not report.get("agreements"):
        lines.extend(["No direct agreements found.", ""])

    lines.extend(["## Disagreements", ""])
    for item in report.get("disagreements", []):
        lines.extend(
            [
                f"### {item.get('section', 'unknown')}",
                f"- Perception signal: {item.get('perception_signal', '')}",
                f"- Reviewer signal: {item.get('reviewer_signal', '')}",
                f"- Interpretation: {item.get('interpretation', '')}",
                "",
            ]
        )
    if not report.get("disagreements"):
        lines.extend(["No major disagreements found.", ""])

    lines.extend(["## Prioritized Improvement Targets", ""])
    for item in report.get("prioritized_targets", []):
        lines.extend(
            [
                f"### Priority {item.get('priority_rank')}: {item.get('section')}",
                f"- Issue type: {item.get('issue_type', '')}",
                "- Evidence:",
            ]
        )
        evidence = item.get("evidence", [])
        lines.extend([f"  - {entry}" for entry in evidence] or ["  - None listed"])
        lines.extend(
            [
                f"- Suggested action: {item.get('suggested_action', '')}",
                f"- Confidence: {item.get('confidence', '')}",
                "- Source signals:",
                f"  - Perception: {item.get('source_signals', {}).get('perception', '')}",
                f"  - Reviewer: {item.get('source_signals', {}).get('reviewer', '')}",
                "",
            ]
        )

    lines.extend(["## Limitations", ""])
    for item in report.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _format_confidence(value: object) -> str:
    if value is None:
        return "not available"
    if isinstance(value, int | float):
        return f"{float(value):.2f}"
    return str(value)
