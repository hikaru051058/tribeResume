"""Run the primary document perception report workflow."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from document_parser import parse_document
from format_fusion_report import format_fusion_report
from fusion_engine import fuse_perception_and_review, load_json
from run_ollama_review import run_review
from run_perception_interpretation import run_perception_interpretation


ROOT = Path(__file__).resolve().parents[1]
HYPOTHESES_PATH = ROOT / "outputs" / "tribe_perception_hypotheses.json"
FUSION_PATH = ROOT / "outputs" / "fusion_report.json"


def _resolve(path: str | Path) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else ROOT / resolved


def _run_probe(input_path: Path, mock: bool, prediction: str | None) -> None:
    command = [
        sys.executable,
        str(ROOT / "src" / "run_tribe_perception_probe.py"),
        "--input",
        str(input_path),
    ]
    if prediction:
        command.extend(["--prediction", prediction])
    if mock:
        command.append("--mock")
    subprocess.run(command, check=True)


def _run_fusion(input_path: Path, review_summary_path: Path) -> None:
    parsed = parse_document(str(input_path))
    report = fuse_perception_and_review(
        perception_hypotheses=load_json(str(HYPOTHESES_PATH)),
        review_summary=load_json(str(review_summary_path)),
        resume_text=parsed["text"],
    )
    report["document_metadata"] = {
        "source_path": parsed["source_path"],
        "file_type": parsed["file_type"],
        "metadata": parsed["metadata"],
        "warnings": parsed["warnings"],
    }
    report["input_paths"] = {
        "perception": str(HYPOTHESES_PATH),
        "review_summary": str(review_summary_path),
    }
    FUSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    FUSION_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    FUSION_PATH.with_suffix(".md").write_text(format_fusion_report(report), encoding="utf-8")
    print(f"Saved fusion JSON: {FUSION_PATH}")
    print(f"Saved fusion Markdown: {FUSION_PATH.with_suffix('.md')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full perception report workflow.")
    parser.add_argument("--input", required=True, help="Path to document/resume input.")
    parser.add_argument("--target-role", default=None)
    parser.add_argument("--model", default="qwen3:14b", help="Ollama model for interpretation.")
    parser.add_argument("--mock", action="store_true", help="Use mock TRIBE-style prediction.")
    parser.add_argument("--prediction", default=None, help="Optional precomputed TRIBE prediction JSON.")
    parser.add_argument("--with-review", action="store_true", help="Also run reviewer agents for comparison.")
    parser.add_argument("--review-profile", default="balanced", choices=["fast", "balanced", "deep", "adaptive"])
    args = parser.parse_args()

    input_path = _resolve(args.input)
    if not args.mock and not args.prediction:
        print("No real TRIBE prediction provided. Use --mock or pass --prediction PATH.")
        return
    if args.mock:
        print("DEMO MODE: mock perception values are not meaningful TRIBE output.")

    _run_probe(input_path=input_path, mock=args.mock, prediction=args.prediction)
    interpretation = run_perception_interpretation(
        input_path=str(input_path),
        features_path=str(HYPOTHESES_PATH),
        model=args.model,
        target_role=args.target_role,
    )
    print(f"Saved interpretation JSON: {interpretation['json_path']}")
    print(f"Saved interpretation Markdown: {interpretation['markdown_path']}")

    if args.with_review:
        review = run_review(
            input_path=str(input_path),
            profile=args.review_profile,
            model_override=None,
            output_prefix="review",
            target_role=args.target_role,
        )
        _run_fusion(input_path=input_path, review_summary_path=Path(review["summary_path"]))


if __name__ == "__main__":
    main()
