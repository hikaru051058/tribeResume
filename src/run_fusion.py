"""Fuse TRIBE perception hypotheses with Ollama review summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from document_parser import parse_document
from format_fusion_report import format_fusion_report
from fusion_engine import fuse_perception_and_review, load_json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "examples" / "resume_sample.txt"
DEFAULT_PERCEPTION = ROOT / "outputs" / "tribe_perception_hypotheses.json"
DEFAULT_REVIEW = ROOT / "outputs" / "hikaru_balanced_ollama_review_summary.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "fusion_report.json"


def _resolve_path(path: str) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else ROOT / resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Fuse perception and review signals.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--perception", default=str(DEFAULT_PERCEPTION))
    parser.add_argument("--review-summary", default=str(DEFAULT_REVIEW))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    input_path = _resolve_path(args.input)
    perception_path = _resolve_path(args.perception)
    review_path = _resolve_path(args.review_summary)
    output_path = _resolve_path(args.output)

    parsed = parse_document(str(input_path))
    report = fuse_perception_and_review(
        perception_hypotheses=load_json(str(perception_path)),
        review_summary=load_json(str(review_path)),
        resume_text=parsed["text"],
    )
    report["document_metadata"] = {
        "source_path": parsed["source_path"],
        "file_type": parsed["file_type"],
        "metadata": parsed["metadata"],
        "warnings": parsed["warnings"],
    }
    report["input_paths"] = {
        "perception": str(perception_path),
        "review_summary": str(review_path),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path = output_path.with_suffix(".md")
    md_path.write_text(format_fusion_report(report), encoding="utf-8")
    print(f"Saved fusion JSON: {output_path}")
    print(f"Saved fusion Markdown: {md_path}")


if __name__ == "__main__":
    main()
