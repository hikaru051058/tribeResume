"""Compare TRIBE-derived perception signals for controlled text variants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from format_variant_comparison import format_variant_comparison


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FACTS = [
    "Dockerized AI-assisted medical reporting platform",
    "Elasticsearch semantic retrieval",
    "Bedrock-backed inference",
    "130,000+",
    "~30%",
    "~2 hours",
    "~6 to ~1",
    "~3.4s",
]


def compare_variant_signals(a_features: dict, b_features: dict) -> dict:
    """Compare section-level proxy features between two variants."""

    a_by_section = _by_section(a_features)
    b_by_section = _by_section(b_features)
    sections = sorted(set(a_by_section) | set(b_by_section))
    rows = [_compare_section(section, a_by_section, b_by_section) for section in sections]
    changed_sections = [
        row
        for row in rows
        if abs(row["delta_cognitive_load_proxy"]) >= 0.05
        or abs(row["delta_position_normalized_salience"]) >= 0.05
        or abs(row["delta_salience_proxy"]) >= 0.05
    ]
    biggest_load_reduction = min(
        rows,
        key=lambda row: row["delta_cognitive_load_proxy"],
        default={},
    )
    biggest_salience_change = max(
        rows,
        key=lambda row: abs(row["delta_position_normalized_salience"]),
        default={},
    )
    facts = _facts_preserved(a_features, b_features)
    return {
        "metadata": {
            "variant_a": a_features.get("metadata", {}).get("source_path"),
            "variant_b": b_features.get("metadata", {}).get("source_path"),
            "caution": (
                "This compares TRIBE-derived proxy signals from synthetic reading events. "
                "It does not validate hiring outcomes or prove one resume is better."
            ),
        },
        "section_signal_changes": rows,
        "changed_sections": changed_sections,
        "biggest_load_reduction": biggest_load_reduction,
        "biggest_salience_change": biggest_salience_change,
        "facts_preserved": facts,
        "interpretation": _interpretation(
            biggest_load_reduction, biggest_salience_change, rows
        ),
        "recommendation": _recommendation(biggest_load_reduction, facts),
        "limitations": [
            "Real TRIBE output is from synthetic reading events, not measured human response.",
            "A lower cognitive-load proxy is not proof of a better resume.",
            "Facts must be manually checked before any wording change is accepted.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare perception signals for two variants.")
    parser.add_argument("--a-features", required=True)
    parser.add_argument("--b-features", required=True)
    parser.add_argument(
        "--output",
        default=str(ROOT / "outputs" / "variant_comparison.json"),
    )
    args = parser.parse_args()

    a_features = _load(args.a_features)
    b_features = _load(args.b_features)
    comparison = compare_variant_signals(a_features, b_features)
    output = _resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
    markdown = output.with_suffix(".md")
    markdown.write_text(format_variant_comparison(comparison), encoding="utf-8")
    print(f"Saved comparison JSON: {output}")
    print(f"Saved comparison Markdown: {markdown}")
    print(
        "Biggest load reduction: "
        f"{comparison['biggest_load_reduction'].get('section', 'not available')}"
    )


def _compare_section(section: str, a_by_section: dict, b_by_section: dict) -> dict:
    a = a_by_section.get(section, {})
    b = b_by_section.get(section, {})
    a_segment_count = _int(a.get("segment_count"))
    b_segment_count = _int(b.get("segment_count"))
    a_duration = _duration(a)
    b_duration = _duration(b)
    a_word_count = _optional_int(a.get("word_count"))
    b_word_count = _optional_int(b.get("word_count"))
    a_load = _num(a.get("cognitive_load_proxy"))
    b_load = _num(b.get("cognitive_load_proxy"))
    delta_load = round(b_load - a_load, 4)
    warnings = _stability_warnings(
        a_segment_count=a_segment_count,
        b_segment_count=b_segment_count,
        a_duration=a_duration,
        b_duration=b_duration,
        delta_load=delta_load,
    )
    return {
        "section": section,
        "a_segment_count": a_segment_count,
        "b_segment_count": b_segment_count,
        "a_section_duration": a_duration,
        "b_section_duration": b_duration,
        "a_word_count": a_word_count,
        "b_word_count": b_word_count,
        "a_load_per_segment": _safe_div(a_load, a_segment_count),
        "b_load_per_segment": _safe_div(b_load, b_segment_count),
        "a_load_per_word": _safe_div(a_load, a_word_count),
        "b_load_per_word": _safe_div(b_load, b_word_count),
        "stability_warning": "; ".join(warnings) if warnings else "",
        "a_response_intensity": _num(a.get("response_intensity")),
        "b_response_intensity": _num(b.get("response_intensity")),
        "delta_response_intensity": round(_num(b.get("response_intensity")) - _num(a.get("response_intensity")), 4),
        "a_salience_proxy": _num(a.get("salience_proxy")),
        "b_salience_proxy": _num(b.get("salience_proxy")),
        "delta_salience_proxy": round(_num(b.get("salience_proxy")) - _num(a.get("salience_proxy")), 4),
        "a_position_normalized_salience": _num(a.get("position_normalized_salience")),
        "b_position_normalized_salience": _num(b.get("position_normalized_salience")),
        "delta_position_normalized_salience": round(
            _num(b.get("position_normalized_salience"))
            - _num(a.get("position_normalized_salience")),
            4,
        ),
        "a_cognitive_load_proxy": a_load,
        "b_cognitive_load_proxy": b_load,
        "delta_cognitive_load_proxy": delta_load,
        "a_underemphasis_proxy": _num(a.get("underemphasis_proxy")),
        "b_underemphasis_proxy": _num(b.get("underemphasis_proxy")),
        "delta_underemphasis_proxy": round(
            _num(b.get("underemphasis_proxy")) - _num(a.get("underemphasis_proxy")),
            4,
        ),
    }


def _by_section(features: dict) -> dict[str, dict]:
    return {
        str(item.get("section", "unknown")).lower(): item
        for item in features.get("section_features", [])
    }


def _facts_preserved(a_features: dict, b_features: dict) -> dict:
    a_path = a_features.get("metadata", {}).get("source_path")
    b_path = b_features.get("metadata", {}).get("source_path")
    a_text = Path(a_path).read_text(encoding="utf-8") if a_path and Path(a_path).exists() else ""
    b_text = Path(b_path).read_text(encoding="utf-8") if b_path and Path(b_path).exists() else ""
    missing = [
        fact for fact in REQUIRED_FACTS if not _contains_fact(a_text, fact) or not _contains_fact(b_text, fact)
    ]
    return {"preserved": not missing, "missing_or_changed_facts": missing}


def _contains_fact(text: str, fact: str) -> bool:
    normalized_text = text.lower().replace("approximately", "~")
    normalized_fact = fact.lower()
    if normalized_fact in normalized_text:
        return True
    aliases = {
        "bedrock-backed inference": ["bedrock-backed inference", "bedrock-backed", "aws bedrock"],
        "elasticsearch semantic retrieval": ["elasticsearch semantic retrieval", "elasticsearch"],
        "~6 to ~1": ["~6 to ~1", "from ~6 to ~1", "6 to 1"],
        "~2 hours": ["~2 hours", "2 hours"],
        "~3.4s": ["~3.4s", "3.4s"],
        "~30%": ["~30%", "30%"],
    }
    return any(alias in normalized_text for alias in aliases.get(normalized_fact, []))


def _interpretation(load_reduction: dict, salience_change: dict, rows: list[dict]) -> list[str]:
    items = []
    if load_reduction:
        delta = load_reduction.get("delta_cognitive_load_proxy", 0.0)
        direction = "reduced" if delta < 0 else "increased"
        items.append(
            f"The clearer version {direction} the proxy load signal for {load_reduction.get('section')} by {abs(delta):.4f}."
        )
        shifted = _large_short_section_increase(rows, exclude=load_reduction.get("section"))
        if delta < 0 and shifted:
            items.append(
                "The target section improved on the load proxy, but signal may have shifted to another section. "
                f"Inspect timeline mapping before treating this as a clean improvement; {shifted.get('section')} increased by "
                f"{shifted.get('delta_cognitive_load_proxy'):+.4f} and has warning: {shifted.get('stability_warning')}."
            )
    if salience_change:
        items.append(
            f"The largest normalized salience shift was in {salience_change.get('section')} ({salience_change.get('delta_position_normalized_salience'):+.4f})."
        )
    items.append("This suggests a possible direction, not a validated quality improvement.")
    return items


def _large_short_section_increase(rows: list[dict], exclude: str | None = None) -> dict:
    candidates = [
        row
        for row in rows
        if row.get("section") != exclude
        and row.get("delta_cognitive_load_proxy", 0.0) >= 0.25
        and (
            min(row.get("a_segment_count", 0), row.get("b_segment_count", 0)) < 5
            or min(row.get("a_section_duration", 0.0), row.get("b_section_duration", 0.0)) <= 5
        )
    ]
    return max(candidates, key=lambda row: row["delta_cognitive_load_proxy"], default={})


def _stability_warnings(
    a_segment_count: int,
    b_segment_count: int,
    a_duration: float,
    b_duration: float,
    delta_load: float,
) -> list[str]:
    warnings = []
    if a_segment_count < 3 or b_segment_count < 3:
        warnings.append("low segment count; proxy may be unstable")
    if _relative_difference(a_segment_count, b_segment_count) > 0.5:
        warnings.append("large segment-count difference; compare cautiously")
    if _relative_difference(a_duration, b_duration) > 0.5:
        warnings.append("large duration difference; wording/timing changed substantially")
    short_section = min(a_segment_count, b_segment_count) < 5 or min(a_duration, b_duration) <= 5
    if abs(delta_load) >= 0.25 and short_section:
        warnings.append("large change in a short section; inspect segment mapping")
    return warnings


def _recommendation(load_reduction: dict, facts: dict) -> str:
    if load_reduction and load_reduction.get("delta_cognitive_load_proxy", 0.0) < 0 and facts.get("preserved"):
        return "Consider the clearer variant as a candidate for manual review because proxy load decreased while required facts appear preserved."
    return "Inspect both variants manually; do not accept a wording change unless facts remain intact."


def _num(value: object) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _optional_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _duration(item: dict) -> float:
    if item.get("section_duration") is not None:
        return _num(item.get("section_duration"))
    start = item.get("start_time", item.get("start"))
    end = item.get("end_time", item.get("stop"))
    return round(max(_num(end) - _num(start), 0.0), 4)


def _safe_div(value: float, denominator: int | None) -> float | None:
    if not denominator:
        return None
    return round(value / denominator, 6)


def _relative_difference(a: float, b: float) -> float:
    a = float(a or 0.0)
    b = float(b or 0.0)
    baseline = max(min(abs(a), abs(b)), 1e-9)
    return abs(a - b) / baseline


def _load(path: str) -> dict:
    return json.loads(_resolve(path).read_text(encoding="utf-8"))


def _resolve(path: str) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else ROOT / resolved


if __name__ == "__main__":
    main()
