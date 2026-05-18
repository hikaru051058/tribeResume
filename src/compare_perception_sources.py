"""Compare mock and real TRIBE perception feature outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from format_perception_source_comparison import format_perception_source_comparison


ROOT = Path(__file__).resolve().parents[1]
METRICS = [
    ("salience_proxy", "Salience Proxy"),
    ("cognitive_load_proxy", "Cognitive Load Proxy"),
    ("underemphasis_proxy", "Underemphasis Proxy"),
]


def load_json(path: str) -> dict:
    """Load a JSON object from an absolute or repo-relative path."""

    resolved = _resolve_path(path)
    return json.loads(resolved.read_text(encoding="utf-8"))


def compare_perception_sources(mock_features: dict, real_features: dict) -> dict:
    """Compare section-level proxy rankings from mock and real feature files."""

    mock_by_section = _features_by_section(mock_features)
    real_by_section = _features_by_section(real_features)
    mock_sections = set(mock_by_section)
    real_sections = set(real_by_section)
    shared_sections = sorted(mock_sections & real_sections)

    ranking_comparisons = [
        _compare_metric(metric, label, mock_by_section, real_by_section, shared_sections)
        for metric, label in METRICS
    ]

    agreements = []
    disagreements = []
    for comparison in ranking_comparisons:
        agreements.extend(comparison["agreements"])
        disagreements.extend(comparison["disagreements"])

    return {
        "metadata": {
            "mock_feature_path": mock_features.get("metadata", {}).get("prediction_path"),
            "real_feature_path": real_features.get("metadata", {}).get("prediction_path"),
            "mock_source": mock_features.get("metadata", {}).get("source", "unknown"),
            "real_source": real_features.get("metadata", {}).get("source", "unknown"),
            "caution": (
                "Mock and real TRIBE-derived proxy signals are not directly equivalent. "
                "Real TRIBE output here comes from synthetic resume-reading events, not "
                "human scans, and neither source validates hiring prediction."
            ),
        },
        "section_overlap": {
            "shared_sections": shared_sections,
            "mock_only_sections": sorted(mock_sections - real_sections),
            "real_only_sections": sorted(real_sections - mock_sections),
            "shared_count": len(shared_sections),
            "mock_section_count": len(mock_sections),
            "real_section_count": len(real_sections),
        },
        "salience_ranking_comparison": _find_metric_comparison(
            ranking_comparisons, "salience_proxy"
        ),
        "cognitive_load_ranking_comparison": _find_metric_comparison(
            ranking_comparisons, "cognitive_load_proxy"
        ),
        "underemphasis_ranking_comparison": _find_metric_comparison(
            ranking_comparisons, "underemphasis_proxy"
        ),
        "ranking_comparisons": ranking_comparisons,
        "sections_where_mock_and_real_agree": agreements,
        "sections_where_mock_and_real_disagree": disagreements,
        "major_agreements": agreements[:10],
        "major_disagreements": disagreements[:10],
        "what_this_suggests": _build_suggestions(shared_sections, agreements, disagreements),
        "what_cannot_be_concluded": [
            "Agreement between mock and real rankings does not prove the mock model is valid.",
            "Real TRIBE output from synthetic reading events is not measured perception.",
            "These proxy rankings do not predict recruiter decisions or resume outcomes.",
            "A section with high proxy salience is not automatically a strong resume section.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare mock and real TRIBE perception feature files."
    )
    parser.add_argument(
        "--mock-features",
        required=True,
        help="Path to mock tribe_perception_features JSON.",
    )
    parser.add_argument(
        "--real-features",
        required=True,
        help="Path to real tribe_perception_features JSON.",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "outputs" / "perception_source_comparison.json"),
        help="Path for comparison JSON output.",
    )
    args = parser.parse_args()

    mock_features = load_json(args.mock_features)
    real_features = load_json(args.real_features)
    comparison = compare_perception_sources(mock_features, real_features)

    output_path = _resolve_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")

    markdown_path = output_path.with_suffix(".md")
    markdown_path.write_text(
        format_perception_source_comparison(comparison), encoding="utf-8"
    )

    overlap = comparison["section_overlap"]
    print(f"Saved comparison JSON: {output_path}")
    print(f"Saved comparison Markdown: {markdown_path}")
    print(
        "Shared sections: "
        f"{overlap['shared_count']} "
        f"(mock={overlap['mock_section_count']}, real={overlap['real_section_count']})"
    )
    print(f"Major agreements: {len(comparison['major_agreements'])}")
    print(f"Major disagreements: {len(comparison['major_disagreements'])}")


def _compare_metric(
    metric: str,
    metric_label: str,
    mock_by_section: dict[str, dict],
    real_by_section: dict[str, dict],
    shared_sections: list[str],
) -> dict:
    mock_ranks = _rank_sections(mock_by_section, metric, shared_sections)
    real_ranks = _rank_sections(real_by_section, metric, shared_sections)
    rows = []
    agreements = []
    disagreements = []

    for section in shared_sections:
        mock_rank = mock_ranks[section]["rank"]
        real_rank = real_ranks[section]["rank"]
        rank_delta = abs(mock_rank - real_rank)
        mock_value = mock_ranks[section]["value"]
        real_value = real_ranks[section]["value"]
        rows.append(
            {
                "section": section,
                "mock_rank": mock_rank,
                "real_rank": real_rank,
                "rank_delta": rank_delta,
                "mock_value": round(mock_value, 4),
                "real_value": round(real_value, 4),
            }
        )
        if rank_delta <= 1:
            agreements.append(
                {
                    "section": section,
                    "metric": metric,
                    "metric_label": metric_label,
                    "mock_rank": mock_rank,
                    "real_rank": real_rank,
                    "why": f"rank delta is {rank_delta}",
                }
            )
        elif rank_delta >= max(2, len(shared_sections) // 3):
            disagreements.append(
                {
                    "section": section,
                    "metric": metric,
                    "metric_label": metric_label,
                    "mock_rank": mock_rank,
                    "real_rank": real_rank,
                    "why": f"rank delta is {rank_delta}",
                }
            )

    rows.sort(key=lambda item: item["real_rank"])
    mean_delta = (
        sum(row["rank_delta"] for row in rows) / len(rows) if rows else 0.0
    )
    return {
        "metric": metric,
        "metric_label": metric_label,
        "rows": rows,
        "mean_rank_delta": round(mean_delta, 4),
        "agreement_summary": _agreement_summary(metric_label, mean_delta, len(rows)),
        "agreements": agreements,
        "disagreements": disagreements,
    }


def _features_by_section(features: dict) -> dict[str, dict]:
    by_section = {}
    for item in features.get("section_features", []):
        section = _normalize_section_name(item.get("section", "unknown"))
        if not section:
            continue
        by_section[section] = {
            **item,
            "section": section,
            "underemphasis_proxy": _underemphasis_value(item),
        }
    return by_section


def _rank_sections(
    features_by_section: dict[str, dict], metric: str, sections: list[str]
) -> dict[str, dict]:
    ranked = sorted(
        (
            {
                "section": section,
                "value": _numeric_value(features_by_section[section], metric),
            }
            for section in sections
        ),
        key=lambda item: (-item["value"], item["section"]),
    )
    return {
        item["section"]: {"rank": index + 1, "value": item["value"]}
        for index, item in enumerate(ranked)
    }


def _underemphasis_value(item: dict[str, Any]) -> float:
    if "underemphasis_proxy" in item:
        return _numeric_value(item, "underemphasis_proxy")
    salience = _numeric_value(item, "salience_proxy")
    load = _numeric_value(item, "cognitive_load_proxy")
    return max(0.0, min(1.0, (1.0 - salience) * 0.7 + load * 0.3))


def _numeric_value(item: dict[str, Any], key: str) -> float:
    value = item.get(key, 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_section_name(name: Any) -> str:
    return str(name or "").strip().lower().replace("_", " ")


def _find_metric_comparison(comparisons: list[dict], metric: str) -> dict:
    for comparison in comparisons:
        if comparison.get("metric") == metric:
            return comparison
    return {}


def _agreement_summary(metric_label: str, mean_delta: float, section_count: int) -> str:
    if section_count == 0:
        return f"No shared sections were available for {metric_label}."
    if mean_delta <= 1.0:
        strength = "high ranking agreement"
    elif mean_delta <= 2.0:
        strength = "moderate ranking agreement"
    else:
        strength = "low ranking agreement"
    return f"{metric_label}: {strength}; mean rank delta {mean_delta:.2f} across {section_count} shared sections."


def _build_suggestions(
    shared_sections: list[str], agreements: list[dict], disagreements: list[dict]
) -> list[str]:
    if not shared_sections:
        return [
            "The files do not share section names, so comparison should start by checking section parsing."
        ]
    suggestions = [
        "Use agreement areas as inspection priorities, not as proof that either signal is correct.",
        "Review disagreement areas manually because mock heuristics and real TRIBE output may be responding to different artifacts.",
    ]
    if agreements:
        top = agreements[0]
        suggestions.append(
            f"The strongest agreement example is {top['section']} on {top['metric_label']}; inspect whether that section is genuinely prominent in the document."
        )
    if disagreements:
        top = disagreements[0]
        suggestions.append(
            f"The strongest disagreement example is {top['section']} on {top['metric_label']}; compare the section timing, density, and real segment alignment."
        )
    return suggestions


def _resolve_path(path: str) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else ROOT / resolved


if __name__ == "__main__":
    main()
