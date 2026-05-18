"""Resume rewrite helpers powered by local Ollama."""

from __future__ import annotations

import json

from ollama_client import call_ollama_chat
from rewrite_schemas import REWRITE_OUTPUT_SCHEMA


def build_rewrite_prompt(
    resume_text: str,
    review_summary: dict,
    target_role: str | None = None,
    rewrite_mode: str = "surgical",
    allow_remove_gpa: bool = False,
    extracted_evidence: dict | None = None,
) -> list[dict]:
    """Build Ollama chat messages for an evidence-preserving resume rewrite."""

    role_context = target_role or "the same general software/technical audience"
    extracted_evidence = extracted_evidence or {}
    gpa_rule = (
        "You may remove GPA only if doing so improves the target-role fit and you explain why."
        if allow_remove_gpa
        else "Never remove GPA. Preserve GPA exactly if it appears."
    )
    mode_rule = (
        "Surgical mode: edit weak bullets only, preserve structure mostly, and preserve all concrete evidence."
        if rewrite_mode == "surgical"
        else "Full mode: broader restructuring is allowed, but concrete evidence still must be preserved unless clearly redundant, misleading, or unsupported."
    )
    system_prompt = f"""You are an evidence-preserving resume rewrite assistant.
Default behavior is surgical editing, not broad rewriting.
You are improving clarity, impact, ATS readability, and bullet structure while preserving proof.
Do not invent companies, schools, dates, metrics, awards, titles, publications, or technologies.
Do not add quantified impact unless it already appears in the resume or summary.
Preserve all numbers and metrics by default.
Preserve all company names, project names, dates, role titles, technical stacks, publication names, dataset/index sizes, latency numbers, pass rates, funding amounts, reductions, and improvements.
Do not delete evidence. Improve wording around evidence instead.
Only remove details if they are clearly redundant, misleading, or unsupported.
Explain every removed metric or evidence item in removed_evidence.
{gpa_rule}
{mode_rule}
If a stronger rewrite would require missing facts, list that in risks_or_assumptions.
Return only JSON matching the provided schema."""

    user_prompt = f"""Target role:
{role_context}

Original resume:
---
{resume_text}
---

Review summary:
{json.dumps(review_summary, indent=2)}

Concrete evidence extracted from original resume:
{json.dumps(extracted_evidence, indent=2)}

Rewrite instructions:
- rewrite_mode must be "{rewrite_mode}".
- Keep the resume concise without deleting proof.
- Preserve section structure in surgical mode.
- Improve weak bullets without adding unsupported facts.
- Make skills and project evidence easier to scan while preserving technical stacks.
- Simplify or soften only claims that are not well supported.
- In preserved_evidence, list important evidence you kept.
- In removed_evidence, list every removed evidence item and the reason.
- In bullet_level_changes, list specific before/after bullet edits.
- In safety_warnings, flag any evidence that might have been weakened.
- Return a complete revised resume in revised_resume_text."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def rewrite_resume_with_ollama(
    resume_text: str,
    review_summary: dict,
    model: str,
    target_role: str | None = None,
    rewrite_mode: str = "surgical",
    allow_remove_gpa: bool = False,
    extracted_evidence: dict | None = None,
) -> dict:
    """Rewrite a resume with Ollama using structured JSON output."""

    response = call_ollama_chat(
        model=model,
        messages=build_rewrite_prompt(
            resume_text,
            review_summary,
            target_role,
            rewrite_mode,
            allow_remove_gpa,
            extracted_evidence,
        ),
        temperature=0.2,
        format_schema=REWRITE_OUTPUT_SCHEMA,
    )
    result = response["parsed"]
    if not isinstance(result, dict):
        result = {"raw_content": str(result)}
    result["model"] = model
    result["target_role"] = target_role
    result["rewrite_mode"] = result.get("rewrite_mode", rewrite_mode)
    result["allow_remove_gpa"] = allow_remove_gpa
    return result
