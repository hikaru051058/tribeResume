"""Ollama interpretation layer for TRIBE-derived perception hypotheses."""

from __future__ import annotations

import json

from explain_tribe_outputs import build_tribe_output_explanation
from ollama_client import call_ollama_chat


PERCEPTION_INTERPRETATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "tribe_output_explanation",
        "overall_perception_summary",
        "section_level_signals",
        "suggestion_priorities",
        "limitations",
    ],
    "properties": {
        "tribe_output_explanation": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "what_raw_output_means",
                "what_features_mean",
                "what_cannot_be_concluded",
            ],
            "properties": {
                "what_raw_output_means": {"type": "string"},
                "what_features_mean": {"type": "string"},
                "what_cannot_be_concluded": {"type": "string"},
            },
        },
        "overall_perception_summary": {"type": "string"},
        "section_level_signals": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "section",
                    "salience_proxy",
                    "cognitive_load_proxy",
                    "underemphasis_proxy",
                    "response_intensity",
                    "evidence_phrases",
                    "possible_meaning",
                    "reader_effect_hypothesis",
                    "suggestion",
                    "caution",
                ],
                "properties": {
                    "section": {"type": "string"},
                    "salience_proxy": {"type": "number"},
                    "cognitive_load_proxy": {"type": "number"},
                    "underemphasis_proxy": {"type": "number"},
                    "response_intensity": {"type": "number"},
                    "evidence_phrases": {"type": "array", "items": {"type": "string"}},
                    "possible_meaning": {"type": "string"},
                    "reader_effect_hypothesis": {"type": "string"},
                    "suggestion": {"type": "string"},
                    "caution": {"type": "string"},
                },
            },
        },
        "suggestion_priorities": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "priority",
                    "section",
                    "suggestion",
                    "why",
                    "source_signals",
                    "reasoning",
                ],
                "properties": {
                    "priority": {"type": "integer"},
                    "section": {"type": "string"},
                    "suggestion": {"type": "string"},
                    "why": {"type": "string"},
                    "source_signals": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "salience_proxy",
                            "cognitive_load_proxy",
                            "underemphasis_proxy",
                            "evidence_phrases",
                        ],
                        "properties": {
                            "salience_proxy": {"type": "number"},
                            "cognitive_load_proxy": {"type": "number"},
                            "underemphasis_proxy": {"type": "number"},
                            "evidence_phrases": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                    "reasoning": {"type": "string"},
                },
            },
        },
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
}


def perception_source_from_hypotheses(perception_hypotheses: dict) -> str:
    """Return mock or real_tribe based on hypothesis metadata."""

    metadata = perception_hypotheses.get("metadata", {})
    if metadata.get("mock") or metadata.get("not_real_tribe_output"):
        return "mock"
    return "real_tribe"


def build_interpretation_prompt(
    resume_text: str,
    perception_hypotheses: dict,
    target_role: str | None = None,
    section_context: list[dict] | None = None,
) -> list[dict]:
    """Build an interpretation prompt from perception hypotheses."""

    system_prompt = """You interpret experimental TRIBE-derived perception hypotheses.
Do not claim this predicts actual hiring outcomes.
Do not claim real brain scans were performed.
Do not claim predicted brain activity equals actual perception.
Interpret predicted or mock response features cautiously.
Use phrases like may suggest, proxy signal, perception hypothesis, predicted response pattern, and experimental signal.
Separate TRIBE-derived signals from text-based reasoning.
Do not invent facts about the resume.
Return only JSON matching the schema."""

    user_prompt = f"""Target role:
{target_role or "not specified"}

Resume text:
---
{resume_text}
---

TRIBE-derived perception hypotheses:
{json.dumps(perception_hypotheses, indent=2)}

Section records that must appear in section_level_signals:
{json.dumps(section_context or [], indent=2)}

Required framing:
- This is a document perception report, not an automatic editor.
- Suggestions should be priorities for the user to consider, not rewritten bullets.
- Do not only summarize one section.
- Produce section_level_signals for every section record provided.
- Preserve the provided salience_proxy, cognitive_load_proxy, underemphasis_proxy, response_intensity, and evidence_phrases values.
- Use the provided proxy values when explaining salience, density, cognitive-load proxy, confusion, or underemphasis hypotheses.
- Cite evidence phrases from the resume text.
- Keep suggestions section-specific and concrete.
- Do not rewrite bullets.
- Do not suggest "use bullet points" if the section already uses bullets.
- Prefer suggestions tied to detected evidence and target role, such as keeping metrics but making the first clause easier to scan, clarifying model/data/evaluation details if available, or grouping skill categories without removing technologies.
- Every suggestion_priority must explain which proxy signal and which evidence phrase caused it.
- Every suggestion_priority must include source_signals copied from the matching section record.
- Use wording like "prioritize inspection" rather than "this will improve hiring outcome."
- For real_tribe reports, tie suggestions directly to rankings:
  - highest salience_proxy: inspect whether the section dominates the first-pass signal.
  - highest cognitive_load_proxy: inspect whether the section is dense, long, or hard to scan.
  - highest underemphasis_proxy: inspect whether important evidence is buried.
- Avoid vague suggestions like "ensure it effectively communicates" unless followed by a specific proxy value and evidence phrase.
- If the source is mock, say the signal is not real TRIBE output.
- Explain what cannot be concluded.
- Do not claim hiring outcome prediction.

Explain what the response-pattern proxy signals may suggest about attention, density, underemphasis, and suggestion priorities."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def interpret_perception_with_ollama(
    resume_text: str,
    perception_hypotheses: dict,
    model: str,
    target_role: str | None = None,
    section_context: list[dict] | None = None,
) -> dict:
    """Interpret perception hypotheses with Ollama."""

    response = call_ollama_chat(
        model=model,
        messages=build_interpretation_prompt(
            resume_text, perception_hypotheses, target_role, section_context
        ),
        temperature=0.2,
        format_schema=PERCEPTION_INTERPRETATION_SCHEMA,
    )
    result = response["parsed"]
    if not isinstance(result, dict):
        result = {"raw_content": str(result)}
    perception_source = perception_source_from_hypotheses(perception_hypotheses)
    result["tribe_output_explanation"] = {
        **result.get("tribe_output_explanation", {}),
        **build_tribe_output_explanation(perception_source),
    }
    result["model"] = model
    result["target_role"] = target_role
    return result
