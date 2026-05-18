"""Generate targeted bullet-level resume patch suggestions."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from bullet_patch import generate_bullet_patches
from document_parser import parse_document
from format_patches import format_patch_report
from patch_validator import RISK_ORDER, validate_patch_evidence_scope


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = ROOT / "examples" / "resume_sample.txt"
PREFERRED_SUMMARY_PATH = ROOT / "outputs" / "hikaru_balanced_ollama_review_summary.json"
DEFAULT_SUMMARY_PATH = ROOT / "outputs" / "ollama_review_summary.json"
PATCH_JSON_PATH = ROOT / "outputs" / "bullet_patches.json"
PATCH_MD_PATH = ROOT / "outputs" / "bullet_patches.md"


def _resolve_summary_path(override: str | None) -> Path | None:
    if override:
        path = Path(override)
        return path if path.is_absolute() else ROOT / path
    if PREFERRED_SUMMARY_PATH.exists():
        return PREFERRED_SUMMARY_PATH
    if DEFAULT_SUMMARY_PATH.exists():
        return DEFAULT_SUMMARY_PATH
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate targeted bullet patches.")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to resume document: .txt, .md, .docx, or text-based .pdf.",
    )
    parser.add_argument(
        "--model",
        default="qwen3:14b",
        help="Ollama model to use for bullet patch generation.",
    )
    parser.add_argument(
        "--target-role",
        default=None,
        help="Target role for patch suggestions.",
    )
    parser.add_argument(
        "--focus",
        default=None,
        help="Patch focus, such as 'AI/ML specificity'.",
    )
    parser.add_argument(
        "--review-summary",
        default=None,
        help="Optional path to a review summary JSON file.",
    )
    parser.add_argument(
        "--fusion-report",
        default=None,
        help="Optional fusion report JSON; top 3 prioritized targets guide patches.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path

    summary_path = _resolve_summary_path(args.review_summary)
    if summary_path is None or not summary_path.exists():
        print(
            "Review summary not found. Run a review first or pass --review-summary PATH."
        )
        return

    parsed = parse_document(str(input_path))
    review_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    fusion_targets = []
    if args.fusion_report:
        fusion_path = Path(args.fusion_report)
        if not fusion_path.is_absolute():
            fusion_path = ROOT / fusion_path
        fusion_report = json.loads(fusion_path.read_text(encoding="utf-8"))
        fusion_targets = fusion_report.get("prioritized_targets", [])[:3]
    result = generate_bullet_patches(
        resume_text=parsed["text"],
        review_summary=review_summary,
        model=args.model,
        target_role=args.target_role,
        focus=args.focus,
        fusion_targets=fusion_targets,
    )
    for patch in result.get("patches", []):
        validation = validate_patch_evidence_scope(parsed["text"], patch)
        patch["validation"] = validation
        model_risk = patch.get("risk_level", "low")
        if RISK_ORDER.get(validation["risk_level"], 1) > RISK_ORDER.get(model_risk, 1):
            patch["risk_level"] = validation["risk_level"]
        if validation["entity_drift"]:
            patch["accept_recommendation"] = "reject"
        elif validation["cross_section_evidence"] and patch.get("accept_recommendation") == "accept":
            patch["accept_recommendation"] = "review"
        elif not validation["valid"] and patch.get("accept_recommendation") == "accept":
            patch["accept_recommendation"] = "review"
    result["document_metadata"] = {
        "source_path": parsed["source_path"],
        "file_type": parsed["file_type"],
        "metadata": parsed["metadata"],
        "warnings": parsed["warnings"],
    }
    result["review_summary_path"] = str(summary_path)
    if args.fusion_report:
        result["fusion_report_path"] = str(fusion_path)
        result["fusion_targets_used"] = fusion_targets

    PATCH_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    PATCH_JSON_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    PATCH_MD_PATH.write_text(format_patch_report(result), encoding="utf-8")

    patches = result.get("patches", [])
    recommendations = Counter(
        patch.get("accept_recommendation", "unknown") for patch in patches
    )
    high_risk = [patch for patch in patches if patch.get("risk_level") == "high"]

    print(f"Patches generated: {len(patches)}")
    print(f"Accept: {recommendations.get('accept', 0)}")
    print(f"Review: {recommendations.get('review', 0)}")
    print(f"Reject: {recommendations.get('reject', 0)}")
    print(f"High-risk patches: {len(high_risk)}")
    for patch in high_risk:
        print(f"- {patch.get('section', 'unknown')}: {patch.get('reason', '')}")
    print(f"Saved JSON: {PATCH_JSON_PATH}")
    print(f"Saved Markdown: {PATCH_MD_PATH}")


if __name__ == "__main__":
    main()
