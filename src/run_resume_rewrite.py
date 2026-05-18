"""Rewrite a resume using local Ollama feedback from prior reviews."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from document_parser import parse_document
from evidence_extractor import extract_resume_evidence
from resume_rewriter import rewrite_resume_with_ollama


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = ROOT / "examples" / "resume_sample.txt"
DEFAULT_SUMMARY_PATH = ROOT / "outputs" / "ollama_review_summary.json"
ORIGINAL_SUMMARY_PATH = ROOT / "outputs" / "original_ollama_review_summary.json"
REVISED_RESUME_PATH = ROOT / "outputs" / "revised_resume.txt"
REWRITE_JSON_PATH = ROOT / "outputs" / "resume_rewrite.json"


def _resolve_review_summary_path() -> Path | None:
    """Find the most recent conventional original review summary path."""

    candidates = [path for path in [DEFAULT_SUMMARY_PATH, ORIGINAL_SUMMARY_PATH] if path.exists()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _missing_evidence(original: dict, revised: dict) -> list[str]:
    revised_lower = "\n".join(revised.get("all", [])).lower()
    missing = []
    for item in original.get("all", []):
        if item.lower() not in revised_lower:
            missing.append(item)
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Rewrite a resume with Ollama.")
    parser.add_argument(
        "--model",
        default="qwen3:14b",
        help="Ollama model to use for rewriting.",
    )
    parser.add_argument(
        "--target-role",
        default=None,
        help="Optional target role, such as 'AI backend engineer intern'.",
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to resume document: .txt, .md, .docx, or text-based .pdf.",
    )
    parser.add_argument(
        "--mode",
        default="surgical",
        choices=["surgical", "full"],
        help="Rewrite mode. Surgical preserves structure and evidence by default.",
    )
    parser.add_argument(
        "--allow-remove-gpa",
        action="store_true",
        help="Allow the rewriter to remove GPA if it explains why.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path

    summary_path = _resolve_review_summary_path()
    if summary_path is None:
        print(
            "Review summary not found. Run the review first, for example:\n"
            "python src/run_ollama_review.py --profile balanced --input examples/resume_sample.txt --output-prefix original"
        )
        return

    parsed_document = parse_document(str(input_path))
    resume_text = parsed_document["text"]
    review_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    original_evidence = extract_resume_evidence(resume_text)

    result = rewrite_resume_with_ollama(
        resume_text=resume_text,
        review_summary=review_summary,
        model=args.model,
        target_role=args.target_role,
        rewrite_mode=args.mode,
        allow_remove_gpa=args.allow_remove_gpa,
        extracted_evidence=original_evidence,
    )
    revised_text = result.get("revised_resume_text", "")
    revised_evidence = extract_resume_evidence(revised_text)
    missing_evidence = _missing_evidence(original_evidence, revised_evidence)

    safety_warnings = list(result.get("safety_warnings", []))
    if missing_evidence:
        safety_warnings.append(
            "Potentially removed concrete evidence: " + "; ".join(missing_evidence[:20])
        )
    if not args.allow_remove_gpa and "gpa" in resume_text.lower() and "gpa" not in revised_text.lower():
        safety_warnings.append("GPA appears to have been removed without --allow-remove-gpa.")
    result["safety_warnings"] = safety_warnings
    result["original_evidence"] = original_evidence
    result["revised_evidence"] = revised_evidence
    result["missing_evidence_after_rewrite"] = missing_evidence
    result["document_metadata"] = {
        "source_path": parsed_document["source_path"],
        "file_type": parsed_document["file_type"],
        "metadata": parsed_document["metadata"],
        "warnings": parsed_document["warnings"],
    }

    REVISED_RESUME_PATH.parent.mkdir(parents=True, exist_ok=True)
    REVISED_RESUME_PATH.write_text(revised_text, encoding="utf-8")
    REWRITE_JSON_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(f"Rewrite mode: {args.mode}")
    print(f"Rewrite confidence: {result.get('rewrite_confidence', 'unknown')}")
    print(f"Preserved evidence items: {len(result.get('preserved_evidence', []))}")
    print(f"Removed evidence items: {len(result.get('removed_evidence', []))}")
    if safety_warnings:
        print("Safety warnings:")
        for warning in safety_warnings:
            print(f"- {warning}")
    print(f"Used review summary: {summary_path}")
    print("Major changes:")
    for change in result.get("major_changes", []):
        print(f"- {change}")
    print(f"Saved revised resume: {REVISED_RESUME_PATH}")
    print(f"Saved rewrite JSON: {REWRITE_JSON_PATH}")


if __name__ == "__main__":
    main()
