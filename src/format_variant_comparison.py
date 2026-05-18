"""Markdown formatting for controlled variant signal comparisons."""

from __future__ import annotations


def format_variant_comparison(comparison: dict) -> str:
    """Render a variant comparison as Markdown."""

    lines = [
        "# Variant Signal Comparison",
        "",
        "## Important Caution",
        "- Real TRIBE output is from synthetic reading events.",
        "- This is not a hiring outcome prediction.",
        "- This is not proof one resume is better.",
        "- The comparison tests whether proxy signals change across controlled wording variants.",
        "",
        "## Variant A vs Variant B",
        f"- Variant A: `{comparison.get('metadata', {}).get('variant_a', 'A')}`",
        f"- Variant B: `{comparison.get('metadata', {}).get('variant_b', 'B')}`",
        f"- Facts preserved: `{comparison.get('facts_preserved', {}).get('preserved', 'unknown')}`",
        "",
        "## Section Signal Changes",
        "",
        "| Section | A Segments | B Segments | A Load | B Load | Delta Load | A Normalized Salience | B Normalized Salience | Delta Salience | Stability Warning |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in comparison.get("section_signal_changes", []):
        lines.append(
            "| {section} | {a_segments} | {b_segments} | {a_load:.4f} | {b_load:.4f} | {delta_load:.4f} | {a_salience:.4f} | {b_salience:.4f} | {delta_salience:.4f} | {warning} |".format(
                section=row.get("section", "unknown"),
                a_segments=row.get("a_segment_count", 0),
                b_segments=row.get("b_segment_count", 0),
                a_load=float(row.get("a_cognitive_load_proxy", 0.0)),
                b_load=float(row.get("b_cognitive_load_proxy", 0.0)),
                delta_load=float(row.get("delta_cognitive_load_proxy", 0.0)),
                a_salience=float(row.get("a_position_normalized_salience", 0.0)),
                b_salience=float(row.get("b_position_normalized_salience", 0.0)),
                delta_salience=float(row.get("delta_position_normalized_salience", 0.0)),
                warning=row.get("stability_warning", ""),
            )
        )

    lines.extend(
        [
            "",
            "## Stability Notes",
            "- Short sections can show unstable load shifts because only a few retained segments determine the section average.",
            "- Segment boundaries matter: a wording change can move content across synthetic time windows even when facts are preserved.",
            "- A load reduction in the target section is useful directional evidence, but it is not proof of quality or real reader preference.",
            "- Large load increases in short sections should be inspected in the timeline report before interpreting the variant as a clean improvement.",
        ]
    )

    lines.extend(["", "## Interpretation"])
    for item in comparison.get("interpretation", []):
        lines.append(f"- {item}")

    lines.extend(["", "## Recommendation"])
    lines.append(comparison.get("recommendation", "Inspect changed sections manually."))

    lines.extend(["", "## Limitations"])
    for item in comparison.get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"
