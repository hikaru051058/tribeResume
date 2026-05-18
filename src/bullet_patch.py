"""Targeted bullet-level patch generation for resumes."""

from __future__ import annotations

import json
import re

from evidence_extractor import extract_resume_evidence
from ollama_client import call_ollama_chat
from patch_schemas import PATCH_OUTPUT_SCHEMA


SECTION_NAMES = {
    "education",
    "experience",
    "projects",
    "skills",
    "publications",
    "awards",
    "coursework",
}


def _line_is_section(line: str) -> bool:
    normalized = line.strip().strip(":").lower()
    return normalized in SECTION_NAMES


def _line_is_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*•]|[0-9]+[.)])\s+", line))


def extract_resume_bullets(text: str) -> list[dict]:
    """Extract bullet-like resume lines with local evidence items."""

    bullets = []
    section_guess = "unknown"
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if _line_is_section(stripped):
            section_guess = stripped.strip(":")
            continue
        if _line_is_bullet(line):
            original = re.sub(r"^\s*(?:[-*•]|[0-9]+[.)])\s+", "", stripped)
            evidence = extract_resume_evidence(original)["all"]
            bullets.append(
                {
                    "section_guess": section_guess,
                    "line_index": index,
                    "original_text": original,
                    "evidence_items": evidence,
                }
            )
    return bullets


def build_patch_prompt(
    resume_text: str,
    review_summary: dict,
    target_role: str | None,
    focus: str | None,
    fusion_targets: list[dict] | None = None,
) -> list[dict]:
    """Build prompt messages for targeted bullet patch generation."""

    bullets = extract_resume_bullets(resume_text)
    evidence = extract_resume_evidence(resume_text)
    role_text = target_role or "the same target role as the resume"
    focus_text = focus or "the weakest areas identified in the review summary"
    fusion_targets = fusion_targets or []

    system_prompt = """You are a targeted resume bullet patch assistant.
Do not rewrite the full resume.
Only suggest bullet-level edits that the user can manually accept or reject.
The original resume is the source of truth.
Never delete metrics, dates, company names, project names, role titles, technologies, or concrete evidence.
Do not invent new metrics, companies, dates, technologies, models, awards, or publications.
If a stronger AI/ML bullet needs missing model/data/evaluation details, ask a missing_info_question instead of inventing.
Return only JSON matching the schema."""

    user_prompt = f"""Target role:
{role_text}

Focus:
{focus_text}

Review summary:
{json.dumps(review_summary, indent=2)}

Fusion targets from TRIBE-style perception + reviewer feedback:
{json.dumps(fusion_targets[:3], indent=2)}

Extracted resume bullets:
{json.dumps(bullets, indent=2)}

Concrete evidence from full resume:
{json.dumps(evidence, indent=2)}

Patch instructions:
- Generate targeted patches only for bullets that need improvement.
- If fusion targets are provided, prioritize the top 3 targets.
- Prefer patches that improve AI/ML specificity, backend ownership, evidence clarity, and ATS scanability.
- Preserve all evidence_items from the original bullet.
- If you reuse evidence from another part of the resume, list it in evidence_added_from_existing_context.
- If any evidence would be removed, list it in evidence_removed and set risk_level to high.
- Use accept only for low-risk patches that preserve evidence.
- Use review when the patch depends on user verification.
- Use reject when the patch would weaken evidence or add unsupported specificity.
- Keep proposed bullets concise and resume-ready."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def generate_bullet_patches(
    resume_text: str,
    review_summary: dict,
    model: str,
    target_role: str | None = None,
    focus: str | None = None,
    fusion_targets: list[dict] | None = None,
) -> dict:
    """Generate targeted bullet patches with Ollama."""

    response = call_ollama_chat(
        model=model,
        messages=build_patch_prompt(
            resume_text, review_summary, target_role, focus, fusion_targets
        ),
        temperature=0.2,
        format_schema=PATCH_OUTPUT_SCHEMA,
    )
    result = response["parsed"]
    if not isinstance(result, dict):
        result = {"raw_content": str(result), "patches": []}
    result.setdefault("target_role", target_role or "")
    result.setdefault("focus", focus or "")
    result["model"] = model
    return result
