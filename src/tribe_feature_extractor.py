"""Feature extraction for TRIBE-style resume perception probes.

These functions are compatible with mock prediction data today and can consume
future real TRIBE prediction outputs after an adapter normalizes them.
"""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path


SECTION_NAMES = {
    "education",
    "experience",
    "projects",
    "skills",
    "publications",
    "awards",
    "coursework",
}


def extract_section_windows(events: list[dict], resume_text: str) -> list[dict]:
    """Estimate section timing windows from word events and resume text."""

    windows = []
    current = {"section": "intro", "start_index": 0, "start_time": 0.0}
    section_by_word_index = {}
    section_names = {name.lower(): name for name in SECTION_NAMES}

    for event in events:
        word = str(event.get("word", "")).strip().lower().strip(":")
        if word in section_names:
            if event.get("index", 0) > current["start_index"]:
                windows.append(
                    {
                        **current,
                        "end_index": event.get("index", 0) - 1,
                        "end_time": event.get("onset", 0.0),
                    }
                )
            current = {
                "section": section_names[word],
                "start_index": event.get("index", 0),
                "start_time": event.get("onset", 0.0),
            }
        section_by_word_index[event.get("index", 0)] = current["section"]

    if events:
        windows.append(
            {
                **current,
                "end_index": events[-1].get("index", 0),
                "end_time": events[-1].get("offset", events[-1].get("onset", 0.0)),
            }
        )

    for window in windows:
        words = [
            event.get("word", "")
            for event in events
            if window["start_index"] <= event.get("index", -1) <= window["end_index"]
        ]
        window["word_count"] = len(words)
        window["text_preview"] = " ".join(words[:30])

    return windows


def compute_response_intensity(prediction: dict) -> dict:
    """Compute global response intensity summary from prediction data."""

    values = [
        float(item.get("response_value", 0.0))
        for item in prediction.get("token_responses", [])
    ]
    if not values:
        return {"mean": 0.0, "max": 0.0, "min": 0.0, "stdev": 0.0}
    return {
        "mean": round(statistics.mean(values), 4),
        "max": round(max(values), 4),
        "min": round(min(values), 4),
        "stdev": round(statistics.pstdev(values), 4),
    }


def _responses_for_window(prediction: dict, window: dict) -> list[dict]:
    return [
        item
        for item in prediction.get("token_responses", [])
        if window["start_index"] <= item.get("index", -1) <= window["end_index"]
    ]


def compute_section_salience(
    prediction: dict, section_windows: list[dict]
) -> list[dict]:
    """Estimate section salience from mean/max pseudo-response intensity."""

    features = []
    for window in section_windows:
        responses = _responses_for_window(prediction, window)
        values = [float(item.get("response_value", 0.0)) for item in responses]
        mean_response = statistics.mean(values) if values else 0.0
        max_response = max(values) if values else 0.0
        features.append(
            {
                **window,
                "mean_response": round(mean_response, 4),
                "max_response": round(max_response, 4),
                "salience_proxy": round((mean_response + max_response) / 2, 4),
            }
        )
    return features


def compute_cognitive_load_proxy(
    prediction: dict, section_windows: list[dict]
) -> list[dict]:
    """Estimate cognitive-load proxy from response variability and density."""

    features = []
    for window in section_windows:
        responses = _responses_for_window(prediction, window)
        values = [float(item.get("response_value", 0.0)) for item in responses]
        variability = statistics.pstdev(values) if len(values) > 1 else 0.0
        duration = max(float(window.get("end_time", 0)) - float(window.get("start_time", 0)), 0.1)
        density = window.get("word_count", 0) / duration
        load_proxy = (variability * 0.6) + min(density / 5.0, 1.0) * 0.4
        features.append(
            {
                "section": window["section"],
                "variability": round(variability, 4),
                "word_density": round(density, 4),
                "cognitive_load_proxy": round(load_proxy, 4),
            }
        )
    return features


def build_perception_hypotheses(section_features: list[dict]) -> list[dict]:
    """Convert section features into cautious perception hypotheses."""

    hypotheses = []
    if not section_features:
        return hypotheses

    saliences = [feature.get("salience_proxy", 0.0) for feature in section_features]
    loads = [feature.get("cognitive_load_proxy", 0.0) for feature in section_features]
    salience_threshold = statistics.mean(saliences)
    load_threshold = statistics.mean(loads) if loads else 0.0

    for feature in section_features:
        section = feature["section"]
        salience = feature.get("salience_proxy", 0.0)
        load = feature.get("cognitive_load_proxy", 0.0)
        notes = []
        if salience >= salience_threshold:
            notes.append("may draw relatively high attention")
        else:
            notes.append("may be underemphasized relative to other sections")
        if load >= load_threshold:
            notes.append("may feel dense or cognitively effortful")
        hypotheses.append(
            {
                "section": section,
                "hypothesis": "; ".join(notes),
                "salience_proxy": salience,
                "position_normalized_salience": feature.get(
                    "position_normalized_salience"
                ),
                "cognitive_load_proxy": load,
                "underemphasis_proxy": feature.get("underemphasis_proxy"),
                "response_intensity": feature.get("response_intensity", feature.get("mean_response")),
                "confidence": "experimental_proxy",
            }
        )
    return hypotheses


def section_features_from_timeline_analysis(timeline_analysis: dict) -> list[dict]:
    """Build perception section features from a timeline analysis report."""

    features = []
    for item in timeline_analysis.get("section_response_summary", []):
        features.append(
            {
                "section": item.get("section", "unknown"),
                "segment_count": item.get("segment_count", 0),
                "mean_response": item.get("average_response_abs_mean", 0.0),
                "response_intensity": item.get("average_response_abs_mean", 0.0),
                "response_variance": item.get("response_variance", 0.0),
                "average_response_std": item.get("average_response_std", 0.0),
                "max_response_abs_mean": item.get("max_response_abs_mean", 0.0),
                "salience_proxy": item.get("salience_proxy", 0.0),
                "position_index": item.get("position_index"),
                "position_normalized_salience": item.get(
                    "position_normalized_salience"
                ),
                "cognitive_load_proxy": item.get("cognitive_load_proxy", 0.0),
                "underemphasis_proxy": item.get("underemphasis_proxy", 0.0),
                "start_time": item.get("start"),
                "end_time": item.get("stop"),
                "source": "real_tribe",
                "feature_source": "timeline_analysis",
                "interpretation_hint": item.get("interpretation_hint", ""),
            }
        )
    return features


def load_real_tribe_prediction(prediction_path: str, segments_path: str) -> dict:
    """Load serialized real TRIBE prediction summary and segment summary."""

    prediction = json.loads(Path(prediction_path).read_text(encoding="utf-8"))
    segments = json.loads(Path(segments_path).read_text(encoding="utf-8"))
    shape = prediction.get("shape") or prediction.get("prediction_shape") or []
    kept_segments = int(shape[0]) if shape else 0
    return {
        "source": "real_tribe",
        "prediction_summary": prediction,
        "segments_summary": segments,
        "prediction_shape": shape,
        "kept_segments": kept_segments,
        "total_segments": _infer_total_segments(segments, kept_segments),
        "segments": _extract_or_reconstruct_segments(segments, kept_segments),
        "caution": (
            "Real TRIBE checkpoint output on synthetic resume-reading events; "
            "not measured brain activity."
        ),
    }


def align_segments_to_sections(
    segments: list[dict], section_windows: list[dict]
) -> list[dict]:
    """Assign real TRIBE time segments to resume sections by temporal overlap."""

    aligned = []
    for segment_index, segment in enumerate(segments):
        segment_start = float(segment.get("start", 0.0))
        segment_end = segment_start + float(segment.get("duration", 1.0))
        best_section = None
        best_overlap = 0.0
        for section in section_windows:
            overlap = max(
                0.0,
                min(segment_end, float(section["end_time"]))
                - max(segment_start, float(section["start_time"])),
            )
            if overlap > best_overlap:
                best_overlap = overlap
                best_section = section
        if best_section is not None:
            aligned.append(
                {
                    **segment,
                    "segment_index": segment_index,
                    "section": best_section["section"],
                    "section_start_time": best_section["start_time"],
                    "section_end_time": best_section["end_time"],
                    "section_word_count": best_section.get("word_count", 0),
                    "section_text_preview": best_section.get("text_preview", ""),
                    "overlap_seconds": round(best_overlap, 4),
                }
            )
    return aligned


def compute_real_response_features(
    prediction_summary: dict, aligned_segments: list[dict]
) -> list[dict]:
    """Compute section-level proxy features from real TRIBE prediction summary."""

    sections: dict[str, list[dict]] = {}
    for segment in aligned_segments:
        sections.setdefault(segment["section"], []).append(segment)

    preview_intensity = _preview_segment_intensity(prediction_summary)
    global_intensity = abs(float(prediction_summary.get("mean", 0.0)))
    global_variance = float(prediction_summary.get("std", 0.0))

    raw_features = []
    for section, section_segments in sections.items():
        segment_indices = [int(item["segment_index"]) for item in section_segments]
        intensities = [
            preview_intensity[index]
            for index in segment_indices
            if index in preview_intensity
        ]
        response_intensity = statistics.mean(intensities) if intensities else global_intensity
        response_variance = statistics.pstdev(intensities) if len(intensities) > 1 else global_variance
        section_start = min(float(item["section_start_time"]) for item in section_segments)
        section_end = max(float(item["section_end_time"]) for item in section_segments)
        duration = max(section_end - section_start, 0.1)
        word_count = _section_word_count(section_segments)
        density = word_count / duration
        raw_features.append(
            {
                "section": section,
                "segment_indices": segment_indices,
                "segment_count": len(section_segments),
                "mean_response": round(response_intensity, 4),
                "response_intensity": round(response_intensity, 4),
                "response_variance": round(response_variance, 4),
                "word_density": round(density, 4),
                "word_count": word_count,
                "start_time": section_start,
                "end_time": section_end,
                "text_preview": _section_text_preview(section_segments),
            }
        )

    if not raw_features:
        return []

    intensities = [item["response_intensity"] for item in raw_features]
    min_intensity = min(intensities)
    max_intensity = max(intensities)
    evidence_flags = {
        item["section"]: _strong_evidence_score(item.get("text_preview", ""))
        for item in raw_features
    }

    features = []
    for item in raw_features:
        salience = _normalize(
            item["response_intensity"], min_intensity, max_intensity
        )
        cognitive_load = min(
            1.0,
            (item["response_variance"] * 0.7)
            + (min(item["word_density"] / 5.0, 1.0) * 0.3),
        )
        underemphasis = max(0.0, (1.0 - salience) * evidence_flags[item["section"]])
        features.append(
            {
                **item,
                "salience_proxy": round(salience, 4),
                "cognitive_load_proxy": round(cognitive_load, 4),
                "underemphasis_proxy": round(underemphasis, 4),
                "source": "real_tribe",
            }
        )
    return features


def _preview_segment_intensity(prediction_summary: dict) -> dict[int, float]:
    intensities = {}
    for index, row in enumerate(prediction_summary.get("preview", [])):
        values = [abs(float(value)) for value in row if isinstance(value, int | float)]
        if values:
            intensities[index] = statistics.mean(values)
    return intensities


def _infer_total_segments(segments_summary: dict | list, kept_segments: int) -> int:
    if isinstance(segments_summary, list):
        return max(len(segments_summary), kept_segments)
    text = segments_summary.get("repr_preview", "")
    match = re.search(r"Predicted\s+\d+\s*/\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return kept_segments * 2 if kept_segments else 0


def _extract_or_reconstruct_segments(
    segments_summary: dict | list, kept_segments: int
) -> list[dict]:
    if isinstance(segments_summary, list):
        normalized = []
        for index, segment in enumerate(segments_summary[:kept_segments or len(segments_summary)]):
            start = _safe_float(segment.get("start"), float(index))
            duration = _safe_float(segment.get("duration"), 1.0)
            normalized.append(
                {
                    "segment_index": int(segment.get("segment_index", index)),
                    "start": start,
                    "duration": duration,
                    "stop": _safe_float(segment.get("stop"), start + duration),
                    "timeline": segment.get("timeline", "resume"),
                }
            )
        return normalized
    text = segments_summary.get("repr_preview", "")
    number_pattern = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?"
    starts = [
        float(match)
        for match in re.findall(rf"start=np\.float64\(({number_pattern})\)", text)
    ]
    durations = [float(match) for match in re.findall(rf"duration=({number_pattern})", text)]
    if len(starts) >= kept_segments and len(durations) >= kept_segments:
        return [
            {"start": starts[index], "duration": durations[index], "timeline": "resume"}
            for index in range(kept_segments)
        ]
    return [
        {"start": float(index), "duration": 1.0, "timeline": "resume"}
        for index in range(kept_segments)
    ]


def _safe_float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _section_word_count(section_segments: list[dict]) -> int:
    return max(int(item.get("section_word_count", 0)) for item in section_segments) or 1


def _section_text_preview(section_segments: list[dict]) -> str:
    preview = section_segments[0].get("section_text_preview", "")
    return preview or f"{section_segments[0]['section']} section aligned to {len(section_segments)} retained TRIBE segments"


def _normalize(value: float, minimum: float, maximum: float) -> float:
    if maximum <= minimum:
        return 0.5
    return (value - minimum) / (maximum - minimum)


def _strong_evidence_score(text: str) -> float:
    if re.search(r"\d|%|\$|\b(?:Python|React|FastAPI|Machine Learning|PostgreSQL|Docker|AWS)\b", text, re.I):
        return 1.0
    return 0.5
