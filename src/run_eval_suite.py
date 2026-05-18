"""Run or inspect the local resume-review evaluation suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from evaluate_outputs import evaluate_review_file
from run_ollama_review import run_review


ROOT = Path(__file__).resolve().parents[1]
EVAL_RESUMES_DIR = ROOT / "examples" / "eval_resumes"
EXPECTATIONS_PATH = ROOT / "examples" / "eval_expectations.yaml"
EVAL_OUTPUT_DIR = ROOT / "outputs" / "eval"
REPORT_JSON_PATH = EVAL_OUTPUT_DIR / "eval_report.json"
REPORT_MD_PATH = EVAL_OUTPUT_DIR / "eval_report.md"


def _resume_key(path: Path) -> str:
    return path.stem


def _review_path_for(resume_key: str) -> Path:
    return EVAL_OUTPUT_DIR / resume_key / "ollama_reviews.json"


def _load_expectations() -> dict:
    if not EXPECTATIONS_PATH.exists():
        return {}
    return yaml.safe_load(EXPECTATIONS_PATH.read_text(encoding="utf-8")) or {}


def _list_eval_resumes(limit: int | None = None) -> list[Path]:
    paths = sorted(
        path
        for path in EVAL_RESUMES_DIR.iterdir()
        if path.suffix.lower() in {".txt", ".md", ".markdown", ".docx", ".pdf"}
    )
    return paths[:limit] if limit is not None else paths


def _write_markdown_report(report: dict) -> None:
    lines = [
        "# Evaluation Report",
        "",
        f"Profile: `{report['profile']}`",
        f"Model override: `{report['model_override']}`",
        f"Skip Ollama: `{report['skip_ollama']}`",
        "",
        "| Resume | Reviews | Issues | Status |",
        "| --- | ---: | ---: | --- |",
    ]
    for item in report["results"]:
        status = "pass" if item.get("passed") else "needs review"
        lines.append(
            f"| {item['resume_key']} | {item.get('review_count', 0)} | "
            f"{item.get('issue_count', 0)} | {status} |"
        )

    lines.extend(["", "## Details", ""])
    for item in report["results"]:
        lines.append(f"### {item['resume_key']}")
        lines.append("")
        if item.get("missing_output"):
            lines.append(f"- Missing output: `{item['review_path']}`")
        lines.append(f"- Expected rating range: `{item.get('expected_rating_range')}`")
        lines.append(f"- Expected flags: `{item.get('expected_flags')}`")
        lines.append(f"- Should not claim: `{item.get('should_not_claim')}`")
        for review in item.get("reviews", []):
            lines.append(
                f"- {review.get('persona')}: {review.get('issue_count', 0)} issues"
            )
            for issue in review.get("issues", []):
                lines.append(f"  - {issue}")
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run resume-review eval suite.")
    parser.add_argument(
        "--profile",
        default="fast",
        choices=["fast", "balanced", "deep", "adaptive"],
        help="Reviewer routing profile.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Manual model override for all reviewer agents.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of eval resumes.",
    )
    parser.add_argument(
        "--skip-ollama",
        action="store_true",
        help="Evaluate existing output files only; do not call Ollama.",
    )
    args = parser.parse_args()

    expectations = _load_expectations()
    EVAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for resume_path in _list_eval_resumes(args.limit):
        key = _resume_key(resume_path)
        resume_output_dir = EVAL_OUTPUT_DIR / key
        review_path = _review_path_for(key)

        if not args.skip_ollama:
            run_review(
                input_path=str(resume_path),
                profile=args.profile,
                model_override=args.model,
                output_prefix=None,
                output_dir=str(resume_output_dir),
            )

        expectation = expectations.get(key, {})
        if not review_path.exists():
            results.append(
                {
                    "resume_key": key,
                    "resume_path": str(resume_path),
                    "review_path": str(review_path),
                    "missing_output": True,
                    "passed": False,
                    "issue_count": 1,
                    "review_count": 0,
                    "expected_rating_range": expectation.get("expected_rating_range"),
                    "expected_flags": expectation.get("expected_flags", []),
                    "should_not_claim": expectation.get("should_not_claim", []),
                    "reviews": [],
                }
            )
            continue

        eval_result = evaluate_review_file(str(review_path))
        eval_result.update(
            {
                "resume_key": key,
                "resume_path": str(resume_path),
                "expected_rating_range": expectation.get("expected_rating_range"),
                "expected_flags": expectation.get("expected_flags", []),
                "should_not_claim": expectation.get("should_not_claim", []),
            }
        )
        results.append(eval_result)

    report = {
        "profile": args.profile,
        "model_override": args.model,
        "skip_ollama": args.skip_ollama,
        "resume_count": len(results),
        "passed_count": sum(1 for item in results if item.get("passed")),
        "issue_count": sum(item.get("issue_count", 0) for item in results),
        "results": results,
    }

    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _write_markdown_report(report)

    print(f"Evaluated resumes: {report['resume_count']}")
    print(f"Passed: {report['passed_count']}")
    print(f"Issues: {report['issue_count']}")
    print(f"Saved JSON report: {REPORT_JSON_PATH}")
    print(f"Saved Markdown report: {REPORT_MD_PATH}")


if __name__ == "__main__":
    main()
