"""Compare original and revised resume drafts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from compare_resumes import compare_resume_texts
from document_parser import parse_document


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ORIGINAL_PATH = ROOT / "examples" / "resume_sample.txt"
DEFAULT_REVISED_PATH = ROOT / "outputs" / "revised_resume.txt"
ORIGINAL_SUMMARY_PATH = ROOT / "outputs" / "ollama_review_summary.json"
PREFIXED_ORIGINAL_SUMMARY_PATH = ROOT / "outputs" / "original_ollama_review_summary.json"
REVISED_SUMMARY_PATH = ROOT / "outputs" / "revised_ollama_review_summary.json"
COMPARISON_PATH = ROOT / "outputs" / "resume_comparison.json"


def _load_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _load_first_existing_json(paths: list[Path]) -> dict | None:
    for path in paths:
        data = _load_json_if_exists(path)
        if data is not None:
            return data
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare original and revised resumes.")
    parser.add_argument(
        "--original",
        default=str(DEFAULT_ORIGINAL_PATH),
        help="Path to original resume text.",
    )
    parser.add_argument(
        "--revised",
        default=str(DEFAULT_REVISED_PATH),
        help="Path to revised resume text.",
    )
    args = parser.parse_args()

    original_path = Path(args.original)
    revised_path = Path(args.revised)
    if not original_path.is_absolute():
        original_path = ROOT / original_path
    if not revised_path.is_absolute():
        revised_path = ROOT / revised_path

    if not revised_path.exists():
        print(
            f"Revised resume not found: {revised_path}\n"
            "Run the rewrite step first:\n"
            "python src/run_resume_rewrite.py --model qwen3:14b"
        )
        return

    comparison = compare_resume_texts(
        original_text=parse_document(str(original_path))["text"],
        revised_text=parse_document(str(revised_path))["text"],
        original_summary=_load_first_existing_json(
            [ORIGINAL_SUMMARY_PATH, PREFIXED_ORIGINAL_SUMMARY_PATH]
        ),
        revised_summary=_load_json_if_exists(REVISED_SUMMARY_PATH),
    )

    COMPARISON_PATH.parent.mkdir(parents=True, exist_ok=True)
    COMPARISON_PATH.write_text(
        json.dumps(comparison, indent=2) + "\n", encoding="utf-8"
    )

    print("Resume comparison summary:")
    print(f"- Clarity: {comparison['clarity_improvement']}")
    print(f"- Credibility: {comparison['credibility_improvement']}")
    print(f"- ATS: {comparison['ats_improvement']}")
    print(f"- Reader response: {comparison['likely_reader_response_change']}")
    print(f"- Recommendation: {comparison['final_recommendation']}")
    print(f"Saved comparison: {COMPARISON_PATH}")


if __name__ == "__main__":
    main()
