"""Markdown formatting for mock-vs-real TRIBE perception comparisons."""

from __future__ import annotations


def format_perception_source_comparison(comparison: dict) -> str:
    """Render a perception source comparison as Markdown."""

    lines = [
        "# Mock vs Real TRIBE Perception Comparison",
        "",
        "## Important Caution",
        "- Mock and real signals are not equivalent.",
        "- Real TRIBE output is from synthetic reading events, not human scans.",
        "- This does not validate hiring prediction.",
        "",
        "## Interpretation",
        _agreement_interpretation(comparison),
        "",
        "## Ranking Agreement",
    ]

    for item in comparison.get("ranking_comparisons", []):
        lines.append(f"### {item.get('metric_label', item.get('metric', 'Metric'))}")
        lines.append("")
        lines.append("| Section | Mock Rank | Real Rank | Delta | Mock Value | Real Value |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        for row in item.get("rows", []):
            lines.append(
                "| {section} | {mock_rank} | {real_rank} | {rank_delta} | {mock_value:.4f} | {real_value:.4f} |".format(
                    section=row.get("section", ""),
                    mock_rank=row.get("mock_rank", ""),
                    real_rank=row.get("real_rank", ""),
                    rank_delta=row.get("rank_delta", ""),
                    mock_value=float(row.get("mock_value") or 0.0),
                    real_value=float(row.get("real_value") or 0.0),
                )
            )
        agreement = item.get("agreement_summary", "")
        if agreement:
            lines.extend(["", agreement])
        lines.append("")

    lines.extend(["## Major Agreements"])
    agreements = comparison.get("major_agreements", [])
    if agreements:
        for agreement in agreements:
            lines.append(
                "- **{section}**: {metric_label} is similarly ranked in mock and real outputs ({why}).".format(
                    section=agreement.get("section", "unknown"),
                    metric_label=agreement.get("metric_label", agreement.get("metric", "metric")),
                    why=agreement.get("why", "rankings are close"),
                )
            )
    else:
        lines.append("- No strong ranking agreements were detected.")
    lines.append("")

    lines.extend(["## Major Disagreements"])
    disagreements = comparison.get("major_disagreements", [])
    if disagreements:
        for disagreement in disagreements:
            lines.append(
                "- **{section}**: {metric_label} differs between mock and real outputs ({why}).".format(
                    section=disagreement.get("section", "unknown"),
                    metric_label=disagreement.get("metric_label", disagreement.get("metric", "metric")),
                    why=disagreement.get("why", "rankings diverge"),
                )
            )
    else:
        lines.append("- No major ranking disagreements were detected.")
    lines.append("")

    lines.extend(["## What This Suggests"])
    for item in comparison.get("what_this_suggests", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.extend(["## What Cannot Be Concluded"])
    for item in comparison.get("what_cannot_be_concluded", []):
        lines.append(f"- {item}")

    return "\n".join(lines).rstrip() + "\n"


def _agreement_interpretation(comparison: dict) -> str:
    agreements = len(comparison.get("major_agreements", []))
    disagreements = len(comparison.get("major_disagreements", []))
    if disagreements >= agreements:
        return (
            "Mock signals are not a reliable substitute for real TRIBE output "
            "in this test."
        )
    return (
        "Mock signals partially align, but still should only be used for "
        "development unless validated further."
    )
