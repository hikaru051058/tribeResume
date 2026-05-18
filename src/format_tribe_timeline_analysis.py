"""Markdown formatter for TRIBE timeline analysis."""

from __future__ import annotations


def format_tribe_timeline_analysis(analysis: dict) -> str:
    """Render TRIBE timeline analysis as Markdown."""

    metadata = analysis.get("metadata", {})
    raw = analysis.get("raw_prediction_summary", {})
    lines = [
        "# TRIBE Timeline Analysis",
        "",
        "## Important Caution",
        f"- Source: `{metadata.get('source', 'unknown')}`.",
        "- Synthetic reading events are used.",
        "- No human scan was performed.",
        "- This is not a hiring prediction or resume-quality judgment.",
        f"- {metadata.get('caution', '')}",
        "",
        "## Analysis Accuracy",
        f"- exact per-segment stats available: `{'yes' if metadata.get('exact_per_segment_stats_available') else 'no'}`",
        f"- approximation used: `{'yes' if metadata.get('approximation_used') else 'no'}`",
        f"- reason: {metadata.get('approximation_reason') or 'Exact compact per-segment stats were provided.'}",
        "",
        "## Raw Prediction Summary",
        f"- prediction shape: `{raw.get('prediction_shape')}`",
        f"- retained segments: `{raw.get('retained_segments')}`",
        f"- output dimensions: `{raw.get('output_dimensions')}`",
        f"- dtype: `{raw.get('dtype')}`",
        f"- min / max: `{raw.get('min')}` / `{raw.get('max')}`",
        f"- mean / std: `{raw.get('mean')}` / `{raw.get('std')}`",
        f"- preview rows available: `{raw.get('preview_rows')}`",
        "",
        "## Position Bias Note",
        "- Synthetic reading events are sequential.",
        "- Early sections may receive high raw salience partly because they occur early in the synthetic timeline.",
        "- Position-normalized salience is a simple heuristic that reduces early-section dominance.",
        "- Use raw and normalized rankings together; neither is a direct measurement of actual reader perception.",
        "",
        "## Segment Timeline",
        "",
        "| Segment | Time Range | Section | Response Abs Mean | Response Std | Stats Source |",
        "| ---: | --- | --- | ---: | ---: | --- |",
    ]

    for segment in analysis.get("segment_timeline", [])[:80]:
        lines.append(
            "| {index} | {start:.2f}-{stop:.2f}s | {section} | {abs_mean:.6f} | {std:.6f} | {source} |".format(
                index=int(segment.get("segment_index", 0)),
                start=float(segment.get("start", 0.0)),
                stop=float(segment.get("stop", 0.0)),
                section=segment.get("mapped_section", "unmapped"),
                abs_mean=float(segment.get("response_abs_mean", 0.0)),
                std=float(segment.get("response_std", 0.0)),
                source=segment.get("stats_source", "unknown"),
            )
        )
    if len(analysis.get("segment_timeline", [])) > 80:
        lines.append("| ... | ... | ... | ... | ... | truncated |")

    lines.extend(
        [
            "",
            "## Section Response Summary",
            "",
            "| Section | Position | Segments | Avg Response Intensity | Raw Salience | Position-Normalized Salience | Response Variance | Load Proxy | Interpretation Hint |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for section in analysis.get("section_response_summary", []):
        lines.append(
            "| {section} | {position} | {count} | {avg:.6f} | {salience:.4f} | {normalized:.4f} | {var:.6f} | {load:.4f} | {hint} |".format(
                section=section.get("section", "unknown"),
                position=section.get("position_index", ""),
                count=section.get("segment_count", 0),
                avg=float(section.get("average_response_abs_mean", 0.0)),
                salience=float(section.get("salience_proxy", 0.0)),
                normalized=float(section.get("position_normalized_salience", 0.0)),
                var=float(section.get("response_variance", 0.0)),
                load=float(section.get("cognitive_load_proxy", 0.0)),
                hint=section.get("interpretation_hint", ""),
            )
        )

    highest = analysis.get("highest_signal_sections", {})
    lines.extend(
        [
            "",
            "## Highest Signal Sections",
            f"- Highest response section: `{highest.get('highest_response_section', 'not available')}`",
            f"- Highest variance section: `{highest.get('highest_variance_section', 'not available')}`",
            f"- Highest load-proxy section: `{highest.get('highest_load_proxy_section', 'not available')}`",
            "",
            "## Limitations",
        ]
    )
    for item in metadata.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"
