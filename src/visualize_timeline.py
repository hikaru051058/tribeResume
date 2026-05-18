from __future__ import annotations

import argparse
from pathlib import Path

from visualization_common import CAUTION_HTML, escape_html, load_json, plotly_script, scatter_by_group, write_html


def build_timeline_html(timeline_path: str, output_path: str) -> None:
    data = load_json(timeline_path)
    segments = data.get("segment_timeline", [])
    if not segments:
        raise ValueError(f"No segment_timeline entries found in {timeline_path}")

    title = "TRIBE Timeline Visualization"
    for segment in segments:
        start = segment.get("start")
        stop = segment.get("stop")
        segment["time_range"] = f"{start} - {stop}"
        segment["mapped_section"] = segment.get("mapped_section") or "unmapped"

    hover = [
        "segment_index",
        "time_range",
        "mapped_section",
        "response_abs_mean",
        "response_std",
        "stats_source",
        "approximate_stats",
        "word_count_in_segment",
    ]
    hover = [field for field in hover if field in segments[0]]
    metadata = data.get("metadata", {})
    summary = data.get("raw_prediction_summary", {})
    section_count = len({segment.get("mapped_section") for segment in segments})
    body = f"""
<section class="hero">
<div class="eyebrow">Timeline</div>
<h1>{title}</h1>
<p class="muted">Each point is a retained TRIBE timestep mapped back to the synthetic resume-reading timeline.</p>
</section>
{CAUTION_HTML}
{plotly_script()}
<div class="grid">
  <div class="card"><div class="muted">Source</div><div class="metric">{escape_html(metadata.get("source", "unknown"))}</div></div>
  <div class="card"><div class="muted">Prediction Shape</div><div class="metric">{escape_html(summary.get("prediction_shape"))}</div></div>
  <div class="card"><div class="muted">Segments</div><div class="metric">{escape_html(len(segments))}</div></div>
  <div class="card"><div class="muted">Mapped Sections</div><div class="metric">{escape_html(section_count)}</div></div>
</div>
<p><strong>Exact per-segment stats:</strong> {escape_html(metadata.get("exact_per_segment_stats_available"))}
 | <strong>Approximation used:</strong> {escape_html(metadata.get("approximation_used"))}</p>
{scatter_by_group("response_abs_mean", segments, "start", "response_abs_mean", "mapped_section", "Segment Response Intensity Over Time", hover)}
{scatter_by_group("response_std", segments, "start", "response_std", "mapped_section", "Segment Response Std Over Time", hover)}
"""
    write_html(output_path, title, body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an interactive TRIBE timeline HTML visualization.")
    parser.add_argument("--timeline", required=True, help="Path to tribe_timeline_analysis.json")
    parser.add_argument("--output", required=True, help="Output standalone HTML path")
    args = parser.parse_args()

    build_timeline_html(args.timeline, args.output)
    print(f"Saved timeline visualization: {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
