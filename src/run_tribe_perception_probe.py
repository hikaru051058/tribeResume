"""Run a TRIBE-style perception probe with mock or precomputed predictions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from document_parser import parse_document
from mock_tribe_prediction import build_mock_prediction
from resume_events import build_fake_word_events
from tribe_feature_extractor import (
    align_segments_to_sections,
    build_perception_hypotheses,
    compute_cognitive_load_proxy,
    compute_real_response_features,
    compute_response_intensity,
    compute_section_salience,
    extract_section_windows,
    load_real_tribe_prediction,
    section_features_from_timeline_analysis,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = ROOT / "examples" / "resume_sample.txt"
EVENTS_PATH = ROOT / "outputs" / "tribe_events.json"
MOCK_PREDICTION_PATH = ROOT / "outputs" / "mock_tribe_prediction.json"
PREDICTION_PATH = ROOT / "outputs" / "tribe_prediction.json"
FEATURES_PATH = ROOT / "outputs" / "tribe_perception_features.json"
HYPOTHESES_PATH = ROOT / "outputs" / "tribe_perception_hypotheses.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TRIBE perception probe.")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to resume/document input.",
    )
    parser.add_argument(
        "--prediction",
        default=None,
        help="Optional precomputed TRIBE-style prediction JSON.",
    )
    parser.add_argument(
        "--real-prediction",
        default=None,
        help="Serialized real TRIBE prediction summary JSON.",
    )
    parser.add_argument(
        "--segments",
        default=None,
        help="Serialized real TRIBE segment summary JSON.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock TRIBE-like prediction data.",
    )
    parser.add_argument(
        "--output-prefix",
        default=None,
        help="Optional prefix for feature/hypothesis outputs.",
    )
    parser.add_argument(
        "--timeline-analysis",
        default=None,
        help="Optional timeline analysis JSON to use for real TRIBE section features.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path

    parsed = parse_document(str(input_path))
    events = build_fake_word_events(parsed["text"])
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVENTS_PATH.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")

    section_windows = extract_section_windows(events, parsed["text"])

    if args.real_prediction:
        if not args.segments:
            raise ValueError("--segments is required with --real-prediction")
        real_prediction_path = _resolve_path(args.real_prediction)
        segments_path = _resolve_path(args.segments)
        real_prediction = load_real_tribe_prediction(
            str(real_prediction_path), str(segments_path)
        )
        timeline_analysis = None
        if args.timeline_analysis:
            timeline_analysis_path = _resolve_path(args.timeline_analysis)
            timeline_analysis = json.loads(timeline_analysis_path.read_text(encoding="utf-8"))
            section_features = section_features_from_timeline_analysis(timeline_analysis)
        else:
            timeline_analysis_path = None
            aligned_segments = align_segments_to_sections(
                real_prediction["segments"], section_windows
            )
            section_features = compute_real_response_features(
                real_prediction["prediction_summary"], aligned_segments
            )
        response_intensity = {
            "mean": real_prediction["prediction_summary"].get("mean", 0.0),
            "max": real_prediction["prediction_summary"].get("max", 0.0),
            "min": real_prediction["prediction_summary"].get("min", 0.0),
            "stdev": real_prediction["prediction_summary"].get("std", 0.0),
        }
        saved_prediction_path = real_prediction_path
        metadata_extra = {
            "source": "real_tribe",
            "mock": False,
            "not_real_tribe_output": False,
            "prediction_shape": real_prediction["prediction_shape"],
            "kept_segments": real_prediction["kept_segments"],
            "total_segments": real_prediction["total_segments"],
            "segments_path": str(segments_path),
            "timeline_analysis_path": str(timeline_analysis_path) if timeline_analysis_path else None,
            "raw_prediction_summary": (timeline_analysis or {}).get("raw_prediction_summary"),
            "caution": real_prediction["caution"],
        }
    elif args.prediction:
        prediction_path = Path(args.prediction)
        if not prediction_path.is_absolute():
            prediction_path = ROOT / prediction_path
        prediction = json.loads(prediction_path.read_text(encoding="utf-8"))
        PREDICTION_PATH.write_text(
            json.dumps(prediction, indent=2) + "\n", encoding="utf-8"
        )
        saved_prediction_path = PREDICTION_PATH
        salience = compute_section_salience(prediction, section_windows)
        load = compute_cognitive_load_proxy(prediction, section_windows)
        load_by_section = {item["section"]: item for item in load}
        section_features = []
        for feature in salience:
            section_features.append({**feature, **load_by_section.get(feature["section"], {})})
        response_intensity = compute_response_intensity(prediction)
        metadata_extra = {
            "source": "mock" if prediction.get("metadata", {}).get("mock") else "unknown",
            "mock": bool(prediction.get("metadata", {}).get("mock", False)),
            "not_real_tribe_output": bool(
                prediction.get("metadata", {}).get("not_real_tribe_output", False)
            ),
        }
    else:
        if not args.mock:
            print("No real TRIBE prediction provided. Using mock mode for development.")
        prediction = build_mock_prediction(events)
        MOCK_PREDICTION_PATH.write_text(
            json.dumps(prediction, indent=2) + "\n", encoding="utf-8"
        )
        saved_prediction_path = MOCK_PREDICTION_PATH
        salience = compute_section_salience(prediction, section_windows)
        load = compute_cognitive_load_proxy(prediction, section_windows)
        load_by_section = {item["section"]: item for item in load}
        section_features = []
        for feature in salience:
            section_features.append({**feature, **load_by_section.get(feature["section"], {})})
        response_intensity = compute_response_intensity(prediction)
        metadata_extra = {
            "source": "mock",
            "mock": bool(prediction.get("metadata", {}).get("mock", False)),
            "not_real_tribe_output": bool(
                prediction.get("metadata", {}).get("not_real_tribe_output", False)
            ),
        }

    features = {
        "metadata": {
            "source_path": parsed["source_path"],
            "file_type": parsed["file_type"],
            "prediction_path": str(saved_prediction_path),
            **metadata_extra,
        },
        "response_intensity": response_intensity,
        "section_windows": section_windows,
        "section_features": section_features,
    }
    hypotheses = {
        "metadata": features["metadata"],
        "hypotheses": build_perception_hypotheses(section_features),
    }

    features_path, hypotheses_path = _output_paths(args.output_prefix)
    features_path.write_text(json.dumps(features, indent=2) + "\n", encoding="utf-8")
    hypotheses_path.write_text(
        json.dumps(hypotheses, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Saved events: {EVENTS_PATH}")
    print(f"Saved prediction: {saved_prediction_path}")
    print(f"Saved features: {features_path}")
    print(f"Saved hypotheses: {hypotheses_path}")


def _resolve_path(path: str) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else ROOT / resolved


def _output_paths(output_prefix: str | None) -> tuple[Path, Path]:
    if not output_prefix:
        return FEATURES_PATH, HYPOTHESES_PATH
    output_dir = ROOT / "outputs"
    return (
        output_dir / f"{output_prefix}_tribe_perception_features.json",
        output_dir / f"{output_prefix}_tribe_perception_hypotheses.json",
    )


if __name__ == "__main__":
    main()
