"""Run timeline and section analysis on saved real TRIBE outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from document_parser import parse_document
from format_tribe_timeline_analysis import format_tribe_timeline_analysis
from tribe_timeline_analysis import (
    build_timeline_analysis,
    load_events_dataframe,
    load_prediction_summary,
    load_segment_stats,
    load_segments_summary,
    section_windows_from_events_dataframe,
)


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze real TRIBE output over a resume timeline.",
        epilog=(
            "Example: python src/run_tribe_timeline_analysis.py "
            "--input examples/resume_sample.txt "
            "--prediction outputs/sample_real_tribe_prediction_raw.json "
            "--segments outputs/sample_real_tribe_segments_summary.json "
            "--segment-stats outputs/sample_real_tribe_segment_stats.json "
            "--events outputs/sample_real_tribe_events_canonical.csv "
            "--output outputs/sample_tribe_timeline_analysis.json"
        ),
    )
    parser.add_argument("--input", required=True, help="Original document/resume path.")
    parser.add_argument("--prediction", required=True, help="Serialized TRIBE prediction summary JSON.")
    parser.add_argument("--segments", required=True, help="Serialized TRIBE segments summary JSON.")
    parser.add_argument(
        "--segment-stats",
        default=None,
        help="Optional exact per-segment prediction stats JSON.",
    )
    parser.add_argument("--events", required=True, help="Canonical TRIBE events CSV.")
    parser.add_argument(
        "--output",
        default=str(ROOT / "outputs" / "tribe_timeline_analysis.json"),
        help="Timeline analysis JSON output path.",
    )
    args = parser.parse_args()

    input_path = _resolve(args.input)
    prediction_path = _resolve(args.prediction)
    segments_path = _resolve(args.segments)
    events_path = _resolve(args.events)
    output_path = _resolve(args.output)

    parsed = parse_document(str(input_path))
    prediction = load_prediction_summary(str(prediction_path))
    segments = load_segments_summary(str(segments_path))
    segment_stats = load_segment_stats(str(_resolve(args.segment_stats))) if args.segment_stats else None
    events_df = load_events_dataframe(str(events_path))
    section_windows = section_windows_from_events_dataframe(events_df)
    analysis = build_timeline_analysis(
        prediction_data=prediction,
        segments=segments,
        events_df=events_df,
        section_windows=section_windows,
        segment_stats_data=segment_stats,
    )
    analysis["input_paths"] = {
        "input": str(input_path),
        "prediction": str(prediction_path),
        "segments": str(segments_path),
        "segment_stats": str(_resolve(args.segment_stats)) if args.segment_stats else None,
        "events": str(events_path),
    }
    analysis["document_metadata"] = {
        "source_path": parsed["source_path"],
        "file_type": parsed["file_type"],
        "metadata": parsed["metadata"],
        "warnings": parsed["warnings"],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    markdown_path = output_path.with_suffix(".md")
    markdown_path.write_text(format_tribe_timeline_analysis(analysis), encoding="utf-8")

    raw = analysis["raw_prediction_summary"]
    section_summary = analysis["section_response_summary"]
    highest_response = max(
        section_summary,
        key=lambda item: item["average_response_abs_mean"],
        default={},
    )
    highest_variance = max(
        section_summary,
        key=lambda item: item["response_variance"],
        default={},
    )
    print(f"Saved timeline analysis JSON: {output_path}")
    print(f"Saved timeline analysis Markdown: {markdown_path}")
    print(f"Prediction shape: {raw.get('prediction_shape')}")
    print(f"Segment count: {raw.get('retained_segments')}")
    print(f"Section count: {len(section_summary)}")
    print(f"Highest response section: {highest_response.get('section', 'not available')}")
    print(f"Highest variance section: {highest_variance.get('section', 'not available')}")


def _resolve(path: str) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else ROOT / resolved


if __name__ == "__main__":
    main()
