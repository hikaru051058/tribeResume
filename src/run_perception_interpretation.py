"""Interpret TRIBE-derived perception hypotheses with Ollama."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from document_parser import parse_document
from format_perception_report import format_perception_report
from perception_interpreter import (
    interpret_perception_with_ollama,
    perception_source_from_hypotheses,
)
from perception_insights import generate_deterministic_insights
from section_evidence import extract_section_evidence, split_document_sections


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = ROOT / "examples" / "resume_sample.txt"
DEFAULT_FEATURES_PATH = ROOT / "outputs" / "tribe_perception_hypotheses.json"
OUTPUT_JSON_PATH = ROOT / "outputs" / "perception_interpretation.json"
OUTPUT_MD_PATH = ROOT / "outputs" / "perception_interpretation.md"
DEFAULT_FULL_FEATURES_PATH = ROOT / "outputs" / "tribe_perception_features.json"


def build_section_context(
    resume_text: str,
    hypotheses: dict,
    features: dict | None = None,
) -> list[dict]:
    """Build deterministic section records for interpretation and reporting."""

    feature_by_section = {
        item.get("section"): item for item in (features or {}).get("section_features", [])
    }
    hypothesis_by_section = {
        item.get("section"): item for item in hypotheses.get("hypotheses", [])
    }
    real_sections = {section["name"] for section in split_document_sections(resume_text)}
    has_coursework_field = bool(extract_section_evidence(resume_text, "coursework", max_items=1))
    sections = []
    for source in [
        (features or {}).get("section_features", []),
        hypotheses.get("hypotheses", []),
    ]:
        for item in source:
            section = item.get("section")
            if section == "coursework" and "coursework" not in real_sections:
                section = "education / coursework" if has_coursework_field else "education"
            if section and section not in sections:
                sections.append(section)

    saliences = [
        float(item.get("salience_proxy", 0.0))
        for item in (features or {}).get("section_features", [])
        if item.get("salience_proxy") is not None
    ]
    if not saliences:
        saliences = [
            float(item.get("salience_proxy", 0.0))
            for item in hypotheses.get("hypotheses", [])
            if item.get("salience_proxy") is not None
        ]
    mean_salience = sum(saliences) / len(saliences) if saliences else 0.0

    records = []
    for section in sections:
        lookup_section = "coursework" if section == "education / coursework" else section
        feature = feature_by_section.get(lookup_section, {})
        hypothesis = hypothesis_by_section.get(lookup_section, {})
        salience = float(feature.get("salience_proxy", hypothesis.get("salience_proxy", 0.0)))
        cognitive_load = float(
            feature.get("cognitive_load_proxy", hypothesis.get("cognitive_load_proxy", 0.0))
        )
        normalized_salience = feature.get(
            "position_normalized_salience",
            hypothesis.get("position_normalized_salience"),
        )
        records.append(
            {
                "section": section,
                "source": feature.get("source") or hypotheses.get("metadata", {}).get("source", "unknown"),
                "salience_proxy": round(salience, 4),
                "position_normalized_salience": round(float(normalized_salience), 4)
                if normalized_salience is not None
                else None,
                "cognitive_load_proxy": round(cognitive_load, 4),
                "underemphasis_proxy": round(max(mean_salience - salience, 0.0), 4),
                "response_intensity": round(float(feature.get("mean_response", 0.0)), 4),
                "hypothesis": hypothesis.get("hypothesis", ""),
                "word_count": feature.get("word_count"),
                "text_preview": feature.get("text_preview", ""),
                "evidence_phrases": extract_section_evidence(resume_text, section, max_items=5),
            }
        )
    return records


def load_full_features(features_path: Path) -> dict | None:
    """Load full perception features when available."""

    candidates = [features_path]
    if features_path.name == "tribe_perception_hypotheses.json":
        candidates.append(features_path.with_name("tribe_perception_features.json"))
    elif features_path.name.endswith("_tribe_perception_hypotheses.json"):
        candidates.append(
            features_path.with_name(
                features_path.name.replace(
                    "_tribe_perception_hypotheses.json",
                    "_tribe_perception_features.json",
                )
            )
        )
    candidates.append(DEFAULT_FULL_FEATURES_PATH)
    for candidate in candidates:
        if candidate.exists() and candidate.name.endswith("tribe_perception_features.json"):
            return json.loads(candidate.read_text(encoding="utf-8"))
    return None


def merge_section_context(result: dict, section_context: list[dict]) -> dict:
    """Ensure every detected section appears with proxy values and evidence."""

    by_section = {
        str(item.get("section", "")).lower(): item
        for item in result.get("section_level_signals", [])
        if item.get("section")
    }
    merged = []
    for record in section_context:
        section_key = str(record["section"]).lower()
        model_item = by_section.get(section_key, {})
        merged.append(
            {
                "section": record["section"],
                "salience_proxy": record["salience_proxy"],
                "position_normalized_salience": record.get("position_normalized_salience"),
                "cognitive_load_proxy": record["cognitive_load_proxy"],
                "underemphasis_proxy": record["underemphasis_proxy"],
                "response_intensity": record["response_intensity"],
                "evidence_phrases": record["evidence_phrases"],
                "possible_meaning": model_item.get("possible_meaning")
                or _default_possible_meaning(record),
                "reader_effect_hypothesis": model_item.get("reader_effect_hypothesis")
                or _default_reader_effect(record),
                "suggestion": model_item.get("suggestion") or _default_suggestion(record),
                "caution": _source_caution(record),
            }
        )
    result["section_level_signals"] = merged
    result["suggestion_priorities"] = _merge_suggestion_priorities(
        result.get("suggestion_priorities", []), merged
    )
    return result


def _default_possible_meaning(record: dict) -> str:
    notes = []
    if record["salience_proxy"] >= 0.7:
        notes.append("may be relatively salient")
    if record["cognitive_load_proxy"] >= 0.37:
        notes.append("may feel dense or effortful to scan")
    if record["underemphasis_proxy"] > 0.05:
        notes.append("may be underemphasized relative to nearby sections")
    return "; ".join(notes) or "shows no strong proxy flag"


def _default_reader_effect(record: dict) -> str:
    return (
        f"The {record['section']} section may shape first-pass perception through "
        f"salience={record['salience_proxy']}, position_normalized_salience="
        f"{record.get('position_normalized_salience')}, and cognitive_load={record['cognitive_load_proxy']}."
    )


def _default_suggestion(record: dict) -> str:
    if record["cognitive_load_proxy"] >= 0.37:
        return "Inspect whether this section can be made easier to scan without removing evidence."
    if record["underemphasis_proxy"] > 0.05:
        return "Inspect whether important evidence in this section should be surfaced more clearly."
    return "Inspect this section for whether the visible evidence matches the target role."


def _default_priorities(section_signals: list[dict]) -> list[dict]:
    ranked = sorted(
        section_signals,
        key=lambda item: item["cognitive_load_proxy"] + item["underemphasis_proxy"],
        reverse=True,
    )
    return [
        {
            "priority": index,
            "section": item["section"],
            "suggestion": item["suggestion"],
            "why": (
                f"Proxy values: salience={item['salience_proxy']}, "
                f"cognitive_load={item['cognitive_load_proxy']}, "
                f"underemphasis={item['underemphasis_proxy']}."
            ),
            "source_signals": _source_signals(item),
            "reasoning": _priority_reasoning(item),
        }
        for index, item in enumerate(ranked[:5], start=1)
    ]


def _merge_suggestion_priorities(
    model_priorities: list[dict], section_signals: list[dict]
) -> list[dict]:
    if not model_priorities:
        return _default_priorities(section_signals)

    by_section = {item["section"].lower(): item for item in section_signals}
    merged = []
    for index, priority in enumerate(model_priorities, start=1):
        section = str(priority.get("section", "")).lower()
        signal = by_section.get(section)
        if signal is None:
            signal = _find_section_signal(priority, section_signals)
        if signal is None:
            continue
        merged.append(
            {
                "priority": priority.get("priority", index),
                "section": signal["section"],
                "suggestion": priority.get("suggestion") or signal["suggestion"],
                "why": priority.get("why") or _priority_reasoning(signal),
                "source_signals": _source_signals(signal),
                "reasoning": _clean_reasoning(
                    priority.get("reasoning"), signal
                )
                or _priority_reasoning(signal),
            }
        )
    return merged or _default_priorities(section_signals)


def _find_section_signal(priority: dict, section_signals: list[dict]) -> dict | None:
    text = " ".join(
        str(priority.get(key, "")) for key in ["section", "suggestion", "why", "reasoning"]
    ).lower()
    for signal in section_signals:
        if signal["section"].lower() in text:
            return signal
    return None


def _source_signals(item: dict) -> dict:
    return {
        "salience_proxy": item["salience_proxy"],
        "position_normalized_salience": item.get("position_normalized_salience"),
        "cognitive_load_proxy": item["cognitive_load_proxy"],
        "underemphasis_proxy": item["underemphasis_proxy"],
        "evidence_phrases": item.get("evidence_phrases", []),
    }


def _priority_reasoning(item: dict) -> str:
    evidence = item.get("evidence_phrases", [])
    evidence_text = f" Evidence used: {evidence[0]}." if evidence else ""
    return (
        f"Prioritize inspection because {item['section']} has "
        f"salience={item['salience_proxy']}, cognitive_load={item['cognitive_load_proxy']}, "
        f"and underemphasis={item['underemphasis_proxy']}.{evidence_text}"
    )


def _clean_reasoning(reasoning: object, signal: dict) -> str | None:
    if not reasoning:
        return None
    text = str(reasoning)
    if signal.get("source") == "real_tribe" and "mock" in text.lower():
        return _priority_reasoning(signal)
    return text


def _source_caution(record: dict) -> str:
    if record.get("source") == "real_tribe":
        return (
            "This uses real TRIBE checkpoint output on synthetic resume-reading events; "
            "it is not measured brain activity or a hiring prediction."
        )
    return "This is a proxy interpretation, not measured reader perception."


def run_perception_interpretation(
    input_path: str,
    features_path: str,
    model: str,
    target_role: str | None = None,
    output_json_path: str | Path = OUTPUT_JSON_PATH,
    output_md_path: str | Path = OUTPUT_MD_PATH,
) -> dict:
    """Run Ollama interpretation and save JSON/Markdown perception reports."""

    resolved_input_path = Path(input_path)
    resolved_features_path = Path(features_path)
    if not resolved_input_path.is_absolute():
        resolved_input_path = ROOT / resolved_input_path
    if not resolved_features_path.is_absolute():
        resolved_features_path = ROOT / resolved_features_path

    parsed = parse_document(str(resolved_input_path))
    hypotheses = json.loads(resolved_features_path.read_text(encoding="utf-8"))
    full_features = load_full_features(resolved_features_path)
    section_context = build_section_context(parsed["text"], hypotheses, full_features)
    result = interpret_perception_with_ollama(
        resume_text=parsed["text"],
        perception_hypotheses=hypotheses,
        model=model,
        target_role=target_role,
        section_context=section_context,
    )
    result = merge_section_context(result, section_context)
    result["deterministic_insights"] = generate_deterministic_insights(
        result.get("section_level_signals", [])
    )
    result["metadata"] = {
        "input_path": str(resolved_input_path),
        "perception_source": perception_source_from_hypotheses(hypotheses),
        "model": model,
        "target_role": target_role,
    }
    result["raw_tribe_signal_summary"] = _raw_tribe_signal_summary(
        hypotheses, full_features
    )
    result["features_path"] = str(resolved_features_path)
    result["document_metadata"] = {
        "source_path": parsed["source_path"],
        "file_type": parsed["file_type"],
        "metadata": parsed["metadata"],
        "warnings": parsed["warnings"],
    }

    output_json = Path(output_json_path)
    output_md = Path(output_md_path)
    if not output_json.is_absolute():
        output_json = ROOT / output_json
    if not output_md.is_absolute():
        output_md = ROOT / output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(format_perception_report(result), encoding="utf-8")
    return {"result": result, "json_path": output_json, "markdown_path": output_md}


def _raw_tribe_signal_summary(hypotheses: dict, full_features: dict | None) -> dict:
    metadata = {}
    metadata.update(hypotheses.get("metadata", {}))
    metadata.update((full_features or {}).get("metadata", {}))
    raw = metadata.get("raw_prediction_summary") or {}
    return {
        "prediction_shape": metadata.get("prediction_shape") or raw.get("prediction_shape"),
        "retained_segments": metadata.get("kept_segments") or raw.get("retained_segments"),
        "total_segments": metadata.get("total_segments"),
        "output_dimensions": raw.get("output_dimensions")
        or _output_dimensions(metadata.get("prediction_shape")),
        "timeline_analysis_path": metadata.get("timeline_analysis_path"),
        "synthetic_event_warning": (
            "Real TRIBE output is computed from synthetic resume-reading events; "
            "no human was scanned."
        ),
    }


def _output_dimensions(shape: object) -> int | None:
    if isinstance(shape, list) and len(shape) > 1:
        return shape[1]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Interpret perception hypotheses.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_PATH))
    parser.add_argument("--features", default=str(DEFAULT_FEATURES_PATH))
    parser.add_argument("--model", default="qwen3:14b")
    parser.add_argument("--target-role", default=None)
    parser.add_argument("--output-json", default=str(OUTPUT_JSON_PATH))
    parser.add_argument("--output-md", default=str(OUTPUT_MD_PATH))
    args = parser.parse_args()

    output = run_perception_interpretation(
        input_path=args.input,
        features_path=args.features,
        model=args.model,
        target_role=args.target_role,
        output_json_path=args.output_json,
        output_md_path=args.output_md,
    )
    print(f"Saved interpretation JSON: {output['json_path']}")
    print(f"Saved interpretation Markdown: {output['markdown_path']}")


if __name__ == "__main__":
    main()
