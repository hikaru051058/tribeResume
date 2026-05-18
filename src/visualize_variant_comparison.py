from __future__ import annotations

import argparse
from pathlib import Path

from visualization_common import (
    CAUTION_HTML,
    bar_chart,
    escape_html,
    grouped_bar_chart,
    load_json,
    plotly_script,
    table_html,
    write_html,
)


def build_variant_comparison_html(comparison_path: str, output_path: str) -> None:
    data = load_json(comparison_path)
    rows = data.get("section_signal_changes", [])
    if not rows:
        raise ValueError(f"No section_signal_changes entries found in {comparison_path}")

    facts = data.get("facts_preserved", {})
    biggest = data.get("biggest_load_reduction") or {}
    warnings = [
        {"section": row.get("section"), "stability_warning": row.get("stability_warning")}
        for row in rows
        if row.get("stability_warning")
    ]
    fig_load = grouped_bar_chart(
        "variant_load",
        rows,
        "section",
        "a_cognitive_load_proxy",
        "b_cognitive_load_proxy",
        "Variant Load Proxy",
    )
    fig_sal = grouped_bar_chart(
        "variant_salience",
        rows,
        "section",
        "a_position_normalized_salience",
        "b_position_normalized_salience",
        "Variant Position-Normalized Salience",
    )
    fig_delta_load = bar_chart(
        "delta_load",
        rows,
        "section",
        "delta_cognitive_load_proxy",
        "Delta Load Proxy",
        [field for field in ["stability_warning", "a_segment_count", "b_segment_count"] if field in rows[0]],
    )
    fig_delta_sal = bar_chart(
        "delta_salience",
        rows,
        "section",
        "delta_position_normalized_salience",
        "Delta Position-Normalized Salience",
        [field for field in ["stability_warning", "a_segment_count", "b_segment_count"] if field in rows[0]],
    )

    warning_html = (
        table_html(warnings, [("section", "Section"), ("stability_warning", "Stability Warning")])
        if warnings
        else "<p>No section stability warnings were recorded.</p>"
    )
    body = f"""
<section class="hero">
<div class="eyebrow">Controlled Variant Experiment</div>
<h1>Variant Signal Comparison</h1>
<p class="muted">Compare section-level proxy shifts between dense and clearer wording variants while preserving factual evidence.</p>
</section>
{CAUTION_HTML}
{plotly_script()}
<div class="grid">
  <div class="card"><div class="muted">Facts Preserved</div><div class="metric">{escape_html(facts.get("preserved"))}</div></div>
  <div class="card"><div class="muted">Biggest Load Reduction</div><div class="metric">{escape_html(biggest.get("section"))}</div></div>
  <div class="card"><div class="muted">Load Delta</div><div class="metric">{escape_html(biggest.get("delta_cognitive_load_proxy"))}</div></div>
  <div class="card"><div class="muted">Stability Warnings</div><div class="metric">{escape_html(len(warnings))}</div></div>
</div>
<h2>Stability Warnings</h2>
{warning_html}
{fig_load}
{fig_sal}
{fig_delta_load}
{fig_delta_sal}
<h2>Interpretation</h2>
<ul>{''.join(f'<li>{escape_html(item)}</li>' for item in data.get('interpretation', []))}</ul>
<h2>Limitations</h2>
<ul>{''.join(f'<li>{escape_html(item)}</li>' for item in data.get('limitations', []))}</ul>
"""
    write_html(output_path, "Variant Signal Comparison", body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create interactive variant comparison charts.")
    parser.add_argument("--comparison", required=True, help="Path to variant_comparison.json")
    parser.add_argument("--output", required=True, help="Output standalone HTML path")
    args = parser.parse_args()

    build_variant_comparison_html(args.comparison, args.output)
    print(f"Saved variant comparison visualization: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
