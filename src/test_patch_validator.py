"""Smoke checks for section-aware bullet patch validation."""

from __future__ import annotations

import json
from pathlib import Path

from patch_validator import validate_patch_evidence_scope


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "examples" / "patch_validation_cases.json"


def main() -> None:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    resume_text = data["resume_text"]
    for case in data["cases"]:
        result = validate_patch_evidence_scope(resume_text, case["patch"])
        print(f"\n{case['name']}")
        print(f"valid: {result['valid']}")
        print(f"risk_level: {result['risk_level']}")
        print(f"issues: {', '.join(result['issues']) or 'none'}")
        if result["cross_section_evidence"]:
            print(f"cross_section_evidence: {result['cross_section_evidence']}")
        if result["unsupported_added_evidence"]:
            print(f"unsupported_added_evidence: {result['unsupported_added_evidence']}")
        if result["entity_drift"]:
            print(f"entity_drift: {result['entity_drift']}")


if __name__ == "__main__":
    main()

