"""Smoke test the local document parser on bundled text and Markdown samples."""

from __future__ import annotations

import json
from pathlib import Path

from document_parser import parse_document


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = [
    ROOT / "examples" / "resume_sample.txt",
    ROOT / "examples" / "resume_sample.md",
]


def main() -> None:
    for sample in SAMPLES:
        parsed = parse_document(str(sample))
        print(f"\n{sample}")
        print(json.dumps(parsed["metadata"], indent=2))
        if parsed["warnings"]:
            print("Warnings:")
            for warning in parsed["warnings"]:
                print(f"- {warning}")


if __name__ == "__main__":
    main()

