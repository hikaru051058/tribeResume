"""Timeline and section analysis helpers for real TRIBE prediction outputs."""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path
from typing import Any

import pandas as pd


def load_prediction_summary(prediction_path: str) -> dict:
    """Load a serialized TRIBE prediction summary."""

    return json.loads(Path(prediction_path).read_text(encoding="utf-8"))


def load_segments_summary(segments_path: str) -> list[dict]:
    """Load or reconstruct TRIBE segment timing records from a summary file."""

    data = json.loads(Path(segments_path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [_normalize_segment(item, index) for index, item in enumerate(data)]

    repr_preview = str(data.get("repr_preview", ""))
    number_pattern = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?"
    starts = [
        float(value)
        for value in re.findall(rf"start=np\.float64\(({number_pattern})\)", repr_preview)
    ]
    durations = [
        float(value)
        for value in re.findall(rf"duration=({number_pattern})", repr_preview)
    ]
    segments = []
    for index, start in enumerate(starts):
        duration = durations[index] if index < len(durations) else 1.0
        segments.append(
            {
                "segment_index": index,
                "start": round(start, 6),
                "duration": duration,
                "stop": round(start + duration, 6),
                "timeline": "resume",
                "source": "segments_summary_repr",
            }
        )
    return segments


def load_events_dataframe(path: str) -> pd.DataFrame:
    """Load canonical TRIBE/neuralset events from CSV."""

    return pd.read_csv(path)


def load_segment_stats(segment_stats_path: str) -> dict:
    """Load compact per-segment TRIBE prediction stats."""

    return json.loads(Path(segment_stats_path).read_text(encoding="utf-8"))


def compute_segment_response_stats(
    prediction_data: dict, segments: list[dict], segment_stats_data: dict | None = None
) -> list[dict]:
    """Compute per-segment response stats from saved prediction data.

    If the saved prediction contains only summary stats plus preview rows, exact
    per-segment stats are available only for previewed rows. Remaining segments
    receive global fallback statistics and are marked as approximate.
    """

    if segment_stats_data:
        return _segment_response_stats_from_file(segment_stats_data, segments)

    shape = prediction_data.get("shape") or prediction_data.get("prediction_shape") or []
    segment_count = int(shape[0]) if shape else len(segments)
    output_dimensions = int(shape[1]) if len(shape) > 1 else None
    normalized_segments = _ensure_segment_count(segments, segment_count)
    preview = prediction_data.get("preview") or []
    global_mean = _float(prediction_data.get("mean"), 0.0)
    global_std = _float(prediction_data.get("std"), 0.0)
    global_min = _float(prediction_data.get("min"), 0.0)
    global_max = _float(prediction_data.get("max"), 0.0)

    results = []
    for index, segment in enumerate(normalized_segments):
        row = preview[index] if index < len(preview) and isinstance(preview[index], list) else None
        if row:
            values = [_float(value, 0.0) for value in row]
            response_mean = statistics.mean(values)
            response_abs_mean = statistics.mean(abs(value) for value in values)
            response_std = statistics.pstdev(values) if len(values) > 1 else 0.0
            response_min = min(values)
            response_max = max(values)
            stats_source = "preview_row"
            approximate = False
        else:
            response_mean = global_mean
            response_abs_mean = abs(global_mean)
            response_std = global_std
            response_min = global_min
            response_max = global_max
            stats_source = "global_summary_fallback"
            approximate = True

        results.append(
            {
                **segment,
                "segment_index": index,
                "response_mean": round(response_mean, 6),
                "response_abs_mean": round(response_abs_mean, 6),
                "response_std": round(response_std, 6),
                "response_min": round(response_min, 6),
                "response_max": round(response_max, 6),
                "output_dimensions": output_dimensions,
                "stats_source": stats_source,
                "approximate_stats": approximate,
            }
        )
    return results


def map_segments_to_sections(
    segments: list[dict], section_windows: list[dict]
) -> list[dict]:
    """Map response segments onto resume section windows by time overlap."""

    mapped = []
    for segment in segments:
        start = _float(segment.get("start"), 0.0)
        stop = _float(segment.get("stop"), start + _float(segment.get("duration"), 1.0))
        best = None
        best_overlap = 0.0
        for section in section_windows:
            section_start = _float(section.get("start_time"), 0.0)
            section_stop = _float(section.get("end_time"), section_start)
            overlap = max(0.0, min(stop, section_stop) - max(start, section_start))
            if overlap > best_overlap:
                best = section
                best_overlap = overlap
        mapped_section = best.get("section", "unmapped") if best else "unmapped"
        mapped.append(
            {
                **segment,
                "mapped_section": mapped_section,
                "section_overlap_seconds": round(best_overlap, 6),
                "word_count_in_segment": _word_count_in_segment(segment, best),
            }
        )
    return mapped


def compute_section_response_summary(mapped_segments: list[dict]) -> list[dict]:
    """Aggregate mapped segment stats by resume section."""

    grouped: dict[str, list[dict]] = {}
    for segment in mapped_segments:
        grouped.setdefault(str(segment.get("mapped_section", "unmapped")), []).append(segment)

    raw = []
    for section, segments in grouped.items():
        abs_means = [_float(item.get("response_abs_mean"), 0.0) for item in segments]
        stds = [_float(item.get("response_std"), 0.0) for item in segments]
        starts = [_float(item.get("start"), 0.0) for item in segments]
        stops = [_float(item.get("stop"), 0.0) for item in segments]
        average_abs = statistics.mean(abs_means) if abs_means else 0.0
        average_std = statistics.mean(stds) if stds else 0.0
        variance = statistics.pstdev(abs_means) if len(abs_means) > 1 else 0.0
        raw.append(
            {
                "section": section,
                "section_start_time": round(min(starts) if starts else 0.0, 6),
                "section_end_time": round(max(stops) if stops else 0.0, 6),
                "section_duration": round(
                    max(max(stops) - min(starts), 0.0) if starts and stops else 0.0,
                    6,
                ),
                "segment_count": len(segments),
                "avg_response_abs_mean": round(average_abs, 6),
                "average_response_abs_mean": round(average_abs, 6),
                "average_response_std": round(average_std, 6),
                "max_response_abs_mean": round(max(abs_means) if abs_means else 0.0, 6),
                "response_variance": round(variance, 6),
                "start": round(min(starts) if starts else 0.0, 6),
                "stop": round(max(stops) if stops else 0.0, 6),
                "approximate_segment_count": sum(
                    1 for item in segments if item.get("approximate_stats")
                ),
            }
        )

    if not raw:
        return []

    intensities = [item["average_response_abs_mean"] for item in raw]
    variances = [item["response_variance"] for item in raw]
    min_intensity, max_intensity = min(intensities), max(intensities)
    min_variance, max_variance = min(variances), max(variances)
    sorted_raw = sorted(raw, key=lambda item: item["start"])
    total_sections = max(len(sorted_raw), 1)
    for position, item in enumerate(sorted_raw, start=1):
        item["salience_proxy"] = round(
            _normalize(item["average_response_abs_mean"], min_intensity, max_intensity), 4
        )
        item["position_index"] = position
        position_factor = (position - 1) / max(total_sections - 1, 1)
        item["position_factor"] = round(position_factor, 4)
        item["position_normalized_salience"] = round(
            min(1.0, max(0.0, item["salience_proxy"] * (0.65 + 0.35 * position_factor))),
            4,
        )
        item["position_normalization_note"] = (
            "Heuristic adjustment that reduces early-section dominance in synthetic "
            "reading timelines; not a TRIBE-native neuroscience metric."
        )
        item["cognitive_load_proxy"] = round(
            min(
                1.0,
                (_normalize(item["response_variance"], min_variance, max_variance) * 0.6)
                + (min(item["average_response_std"], 1.0) * 0.4),
            ),
            4,
        )
        item["underemphasis_proxy"] = round(max(0.0, 1.0 - item["salience_proxy"]) * 0.5, 4)
        item["interpretation_hint"] = _interpretation_hint(item)
    return sorted_raw


def section_windows_from_events_dataframe(events_df: pd.DataFrame) -> list[dict]:
    """Build section timing windows from canonical Word events."""

    from tribe_feature_extractor import extract_section_windows

    words = events_df[events_df["type"] == "Word"].copy()
    events = []
    for _, row in words.iterrows():
        start = _float(row.get("start"), 0.0)
        duration = _float(row.get("duration"), 0.0)
        word_index = int(_float(row.get("word_index"), len(events)))
        events.append(
            {
                "word": str(row.get("text", "")),
                "onset": start,
                "duration": duration,
                "offset": _float(row.get("stop"), start + duration),
                "index": word_index,
            }
        )
    resume_text = " ".join(event["word"] for event in events)
    return extract_section_windows(events, resume_text)


def build_timeline_analysis(
    prediction_data: dict,
    segments: list[dict],
    events_df: pd.DataFrame,
    section_windows: list[dict] | None = None,
    segment_stats_data: dict | None = None,
) -> dict:
    """Build a complete raw/segment/section TRIBE timeline analysis object."""

    windows = section_windows or section_windows_from_events_dataframe(events_df)
    segment_stats = compute_segment_response_stats(
        prediction_data, segments, segment_stats_data=segment_stats_data
    )
    mapped_segments = map_segments_to_sections(segment_stats, windows)
    section_summary = compute_section_response_summary(mapped_segments)
    shape = (
        prediction_data.get("shape")
        or prediction_data.get("prediction_shape")
        or (segment_stats_data or {}).get("prediction_shape")
        or []
    )
    exact_segment_stats = bool(segment_stats_data)
    return {
        "metadata": {
            "source": "real_tribe",
            "synthetic_reading_events": True,
            "position_normalized_salience": {
                "enabled": True,
                "method": (
                    "raw salience multiplied by a simple section-position factor "
                    "that reduces early-section dominance"
                ),
                "caution": "This is a transparent product heuristic, not neuroscience.",
            },
            "exact_per_segment_stats_available": exact_segment_stats,
            "approximation_used": not exact_segment_stats,
            "approximation_reason": None
            if exact_segment_stats
            else "No per-segment stats file was provided; non-preview segments use global fallback stats.",
            "caution": (
                "Real TRIBE checkpoint output on synthetic resume-reading events; "
                "no human was scanned and this is not a hiring prediction."
            ),
            "limitations": _limitations(prediction_data, segment_stats, exact_segment_stats),
        },
        "raw_prediction_summary": {
            "prediction_shape": shape,
            "retained_segments": int(shape[0]) if shape else len(segment_stats),
            "output_dimensions": int(shape[1]) if len(shape) > 1 else None,
            "dtype": prediction_data.get("dtype"),
            "min": prediction_data.get("min"),
            "max": prediction_data.get("max"),
            "mean": prediction_data.get("mean"),
            "std": prediction_data.get("std"),
            "preview_rows": len(prediction_data.get("preview") or []),
            "segment_stats_source": "per_segment_stats_file"
            if exact_segment_stats
            else "prediction_summary_preview_fallback",
        },
        "section_windows": windows,
        "segment_timeline": mapped_segments,
        "section_response_summary": section_summary,
        "highest_signal_sections": _highest_signal_sections(section_summary),
    }


def _normalize_segment(segment: Any, index: int) -> dict:
    if isinstance(segment, dict):
        start = _float(segment.get("start"), float(index))
        duration = _float(segment.get("duration"), 1.0)
        return {
            **segment,
            "segment_index": int(segment.get("segment_index", index)),
            "start": start,
            "duration": duration,
            "stop": _float(segment.get("stop"), start + duration),
        }
    return {
        "segment_index": index,
        "start": float(index),
        "duration": 1.0,
        "stop": float(index + 1),
        "source": "reconstructed",
    }


def _segment_response_stats_from_file(
    segment_stats_data: dict, segments: list[dict]
) -> list[dict]:
    stats = segment_stats_data.get("per_segment_stats", [])
    shape = segment_stats_data.get("prediction_shape") or segment_stats_data.get("global_stats", {}).get("shape") or []
    output_dimensions = int(shape[1]) if len(shape) > 1 else None
    normalized_segments = _ensure_segment_count(segments, len(stats))
    results = []
    for index, stat in enumerate(stats):
        segment = normalized_segments[index] if index < len(normalized_segments) else {}
        results.append(
            {
                **segment,
                "segment_index": int(stat.get("segment_index", index)),
                "response_mean": _float(stat.get("response_mean"), 0.0),
                "response_abs_mean": _float(stat.get("response_abs_mean"), 0.0),
                "response_std": _float(stat.get("response_std"), 0.0),
                "response_min": _float(stat.get("response_min"), 0.0),
                "response_max": _float(stat.get("response_max"), 0.0),
                "response_l2_norm": _float(stat.get("response_l2_norm"), 0.0),
                "positive_fraction": _float(stat.get("positive_fraction"), 0.0),
                "negative_fraction": _float(stat.get("negative_fraction"), 0.0),
                "top_abs_values_preview": stat.get("top_abs_values_preview", []),
                "output_dimensions": output_dimensions,
                "stats_source": "per_segment_stats",
                "approximate_stats": False,
            }
        )
    return results


def _ensure_segment_count(segments: list[dict], segment_count: int) -> list[dict]:
    existing = [_normalize_segment(segment, index) for index, segment in enumerate(segments)]
    if segment_count <= len(existing):
        return existing[:segment_count]
    duration = existing[-1].get("duration", 1.0) if existing else 1.0
    for index in range(len(existing), segment_count):
        existing.append(
            {
                "segment_index": index,
                "start": float(index),
                "duration": duration,
                "stop": float(index) + duration,
                "source": "reconstructed_from_prediction_shape",
            }
        )
    return existing


def _word_count_in_segment(segment: dict, section: dict | None) -> int | None:
    if not section:
        return None
    start = _float(segment.get("start"), 0.0)
    stop = _float(segment.get("stop"), start + _float(segment.get("duration"), 1.0))
    section_start = _float(section.get("start_time"), 0.0)
    section_stop = _float(section.get("end_time"), section_start)
    section_words = int(section.get("word_count", 0) or 0)
    section_duration = max(section_stop - section_start, 0.001)
    overlap = max(0.0, min(stop, section_stop) - max(start, section_start))
    return round(section_words * (overlap / section_duration))


def _highest_signal_sections(section_summary: list[dict]) -> dict:
    if not section_summary:
        return {}
    return {
        "highest_response_section": max(
            section_summary, key=lambda item: item["average_response_abs_mean"]
        ).get("section"),
        "highest_variance_section": max(
            section_summary, key=lambda item: item["response_variance"]
        ).get("section"),
        "highest_load_proxy_section": max(
            section_summary, key=lambda item: item["cognitive_load_proxy"]
        ).get("section"),
    }


def _limitations(
    prediction_data: dict, segment_stats: list[dict], exact_segment_stats: bool = False
) -> list[str]:
    limitations = [
        "Synthetic reading events may not match naturalistic text, audio, or video stimuli.",
        "Section-level aggregation is a product proxy, not a native TRIBE label.",
    ]
    if exact_segment_stats:
        limitations.append(
            "Exact compact per-segment statistics were used, but section-level interpretation remains a proxy."
        )
    elif len(prediction_data.get("preview") or []) < len(segment_stats):
        limitations.append(
            "The saved prediction file contains summary statistics and preview rows, not the full raw array; non-preview segment stats use global fallback values."
        )
    return limitations


def _interpretation_hint(item: dict) -> str:
    if item["salience_proxy"] >= 0.75 and item["cognitive_load_proxy"] >= 0.5:
        return "High proxy salience and higher load; inspect whether the section is prominent but dense."
    if item["salience_proxy"] >= 0.75:
        return "Higher proxy salience; inspect whether this section dominates the first-pass signal."
    if item["cognitive_load_proxy"] >= 0.5:
        return "Higher load proxy; inspect whether the section is dense or hard to scan."
    return "No strong section-level proxy flag; inspect in context."


def _normalize(value: float, minimum: float, maximum: float) -> float:
    if maximum <= minimum:
        return 0.5
    return (value - minimum) / (maximum - minimum)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
