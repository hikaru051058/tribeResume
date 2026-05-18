from __future__ import annotations

import argparse
from pathlib import Path

from visualization_common import CAUTION_HTML, PROXY_DEFINITIONS, bar_chart, escape_html, load_json, plotly_script, write_html


METRICS = [
    "response_intensity",
    "salience_proxy",
    "position_normalized_salience",
    "cognitive_load_proxy",
    "underemphasis_proxy",
]


def build_section_signals_html(features_path: str, output_path: str) -> None:
    data = load_json(features_path)
    sections = data.get("section_features", [])
    if not sections:
        raise ValueError(f"No section_features entries found in {features_path}")

    source = data.get("metadata", {}).get("source", "unknown")
    top_load = max(sections, key=lambda row: row.get("cognitive_load_proxy") or 0)
    top_salience = max(sections, key=lambda row: row.get("salience_proxy") or 0)
    parts = [
        "<section class=\"hero\">",
        "<div class=\"eyebrow\">Section Signals</div>",
        "<h1>Section Signal Dashboard</h1>",
        "<p class=\"muted\">Section-level proxy values derived from TRIBE timeline aggregation.</p>",
        "</section>",
        CAUTION_HTML,
        plotly_script(),
        "<div class=\"grid\">",
        f"<div class=\"card\"><div class=\"muted\">Source</div><div class=\"metric\">{escape_html(source)}</div></div>",
        f"<div class=\"card\"><div class=\"muted\">Sections</div><div class=\"metric\">{escape_html(len(sections))}</div></div>",
        f"<div class=\"card\"><div class=\"muted\">Highest Load</div><div class=\"metric\">{escape_html(top_load.get('section'))}</div></div>",
        f"<div class=\"card\"><div class=\"muted\">Highest Raw Salience</div><div class=\"metric\">{escape_html(top_salience.get('section'))}</div></div>",
        "</div>",
        "<h2>Proxy Definitions</h2>",
        "<ul>",
    ]
    for metric in METRICS:
        parts.append(f"<li><code>{metric}</code>: {escape_html(PROXY_DEFINITIONS.get(metric, ''))}</li>")
    parts.append("</ul>")

    for metric in METRICS:
        if not any(metric in row and row.get(metric) is not None for row in sections):
            continue
        parts.append(
            bar_chart(
                f"section_{metric}",
                sections,
                "section",
                metric,
                metric.replace("_", " ").title(),
                [field for field in ["segment_count", "start_time", "end_time", "source"] if field in sections[0]],
            )
        )

    write_html(output_path, "Section Signal Dashboard", "\n".join(parts))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create interactive section-level TRIBE proxy charts.")
    parser.add_argument("--features", required=True, help="Path to tribe_perception_features.json")
    parser.add_argument("--output", required=True, help="Output standalone HTML path")
    args = parser.parse_args()

    build_section_signals_html(args.features, args.output)
    print(f"Saved section signal visualization: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
